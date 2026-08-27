require('dotenv').config();
const express = require('express');
const session = require('express-session');
const pgSession = require('connect-pg-simple')(session);
const bcrypt = require('bcryptjs');
const helmet = require('helmet');
const { Pool } = require('pg');
const path = require('path');

const app = express();
const PORT = Number(process.env.PORT || 3000);
const isProd = process.env.NODE_ENV === 'production';

if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL is required');
if (!process.env.SESSION_SECRET) throw new Error('SESSION_SECRET is required');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000
});

app.set('trust proxy', 1);
app.use(helmet({ contentSecurityPolicy: false }));
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: false }));
app.use(session({
  store: new pgSession({ pool, tableName: 'china_thread_sessions', createTableIfMissing: true }),
  name: 'thread.sid',
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, sameSite: 'lax', secure: isProd, maxAge: 1000 * 60 * 60 * 12 }
}));

async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS china_thread_users (
      id SERIAL PRIMARY KEY,
      username VARCHAR(80) UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      display_name VARCHAR(120) NOT NULL,
      role VARCHAR(20) NOT NULL DEFAULT 'sales' CHECK (role IN ('admin','manager','sales')),
      is_active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS china_thread_doctors (
      id SERIAL PRIMARY KEY,
      name VARCHAR(120) NOT NULL,
      birth_date DATE,
      age INTEGER,
      gender VARCHAR(20),
      province VARCHAR(80),
      city VARCHAR(80),
      institution VARCHAR(180),
      family_status TEXT,
      interests TEXT,
      owner VARCHAR(120),
      binding_status VARCHAR(30) NOT NULL DEFAULT '未接觸',
      cumulative_cases INTEGER NOT NULL DEFAULT 0,
      monthly_cases INTEGER NOT NULL DEFAULT 0,
      quarterly_cases INTEGER NOT NULL DEFAULT 0,
      yearly_cases INTEGER NOT NULL DEFAULT 0,
      yoy NUMERIC(8,2) NOT NULL DEFAULT 0,
      qoq NUMERIC(8,2) NOT NULL DEFAULT 0,
      mom NUMERIC(8,2) NOT NULL DEFAULT 0,
      last_visit DATE,
      next_visit DATE,
      next_action TEXT,
      monthly_target INTEGER NOT NULL DEFAULT 0,
      monthly_actual INTEGER NOT NULL DEFAULT 0,
      binding_date DATE,
      lost_date DATE,
      created_by INTEGER REFERENCES china_thread_users(id),
      updated_by INTEGER REFERENCES china_thread_users(id),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS china_thread_institutions (
      id SERIAL PRIMARY KEY,
      name VARCHAR(180) NOT NULL,
      address TEXT,
      province VARCHAR(80),
      city VARCHAR(80),
      contact_name VARCHAR(120),
      contact_info VARCHAR(180),
      owner VARCHAR(120),
      binding_status VARCHAR(30) NOT NULL DEFAULT '未接觸',
      cumulative_cases INTEGER NOT NULL DEFAULT 0,
      monthly_cases INTEGER NOT NULL DEFAULT 0,
      quarterly_cases INTEGER NOT NULL DEFAULT 0,
      yearly_cases INTEGER NOT NULL DEFAULT 0,
      yoy NUMERIC(8,2) NOT NULL DEFAULT 0,
      qoq NUMERIC(8,2) NOT NULL DEFAULT 0,
      mom NUMERIC(8,2) NOT NULL DEFAULT 0,
      last_visit DATE,
      next_visit DATE,
      next_action TEXT,
      monthly_target INTEGER NOT NULL DEFAULT 0,
      monthly_actual INTEGER NOT NULL DEFAULT 0,
      binding_date DATE,
      lost_date DATE,
      created_by INTEGER REFERENCES china_thread_users(id),
      updated_by INTEGER REFERENCES china_thread_users(id),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS china_thread_audit_logs (
      id BIGSERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES china_thread_users(id),
      action VARCHAR(50) NOT NULL,
      entity_type VARCHAR(30) NOT NULL,
      entity_id INTEGER,
      detail JSONB,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);

  const username = process.env.ADMIN_USERNAME || 'admin';
  const password = process.env.ADMIN_PASSWORD;
  if (password) {
    const exists = await pool.query('SELECT id FROM china_thread_users WHERE username=$1', [username]);
    if (!exists.rowCount) {
      const hash = await bcrypt.hash(password, 12);
      await pool.query('INSERT INTO china_thread_users(username,password_hash,display_name,role) VALUES($1,$2,$3,$4)', [username, hash, '系統管理員', 'admin']);
      console.log(`Seeded admin user: ${username}`);
    }
  }
}

function auth(req, res, next) {
  if (!req.session.user) return res.status(401).json({ error: 'UNAUTHORIZED' });
  next();
}
function adminOnly(req, res, next) {
  if (!req.session.user || req.session.user.role !== 'admin') return res.status(403).json({ error: 'FORBIDDEN' });
  next();
}
const statuses = new Set(['未接觸','接觸中','試用','合作','核心綁定','流失']);
const cleanInt = v => Math.max(0, Number.parseInt(v, 10) || 0);
const cleanNum = v => Number.isFinite(Number(v)) ? Number(v) : 0;
const nullable = v => (v === '' || v === undefined || v === null) ? null : v;
function normalized(body, type) {
  const base = {
    name: String(body.name || '').trim(), province: String(body.province || '').trim(), city: String(body.city || '').trim(),
    owner: String(body.owner || '').trim(), binding_status: statuses.has(body.binding_status) ? body.binding_status : '未接觸',
    cumulative_cases: cleanInt(body.cumulative_cases), monthly_cases: cleanInt(body.monthly_cases), quarterly_cases: cleanInt(body.quarterly_cases), yearly_cases: cleanInt(body.yearly_cases),
    yoy: cleanNum(body.yoy), qoq: cleanNum(body.qoq), mom: cleanNum(body.mom), last_visit: nullable(body.last_visit), next_visit: nullable(body.next_visit),
    next_action: String(body.next_action || '').trim(), monthly_target: cleanInt(body.monthly_target), monthly_actual: cleanInt(body.monthly_actual),
    binding_date: nullable(body.binding_date), lost_date: nullable(body.lost_date)
  };
  if (type === 'doctor') Object.assign(base, { birth_date: nullable(body.birth_date), age: nullable(body.age) ? cleanInt(body.age) : null, gender: String(body.gender || '').trim(), institution: String(body.institution || '').trim(), family_status: String(body.family_status || '').trim(), interests: String(body.interests || '').trim() });
  else Object.assign(base, { address: String(body.address || '').trim(), contact_name: String(body.contact_name || '').trim(), contact_info: String(body.contact_info || '').trim() });
  return base;
}
async function log(req, action, entityType, entityId, detail={}) { await pool.query('INSERT INTO china_thread_audit_logs(user_id,action,entity_type,entity_id,detail) VALUES($1,$2,$3,$4,$5)', [req.session.user.id, action, entityType, entityId, detail]); }

app.get('/api/health', async (_req,res)=>{ try { await pool.query('SELECT 1'); res.json({ok:true}); } catch(e){ res.status(500).json({ok:false}); } });
app.post('/api/login', async (req,res)=>{ const username=String(req.body.username||'').trim(); const result=await pool.query('SELECT * FROM china_thread_users WHERE username=$1 AND is_active=TRUE',[username]); if(!result.rowCount || !(await bcrypt.compare(String(req.body.password||''), result.rows[0].password_hash))) return res.status(401).json({error:'帳號或密碼錯誤'}); const u=result.rows[0]; req.session.user={id:u.id,username:u.username,display_name:u.display_name,role:u.role}; res.json({user:req.session.user}); });
app.post('/api/logout', auth, (req,res)=>req.session.destroy(()=>res.json({ok:true})));
app.get('/api/me', auth, (req,res)=>res.json({user:req.session.user}));

app.get('/api/users', auth, adminOnly, async (_req,res)=>{const q=await pool.query('SELECT id,username,display_name,role,is_active,created_at FROM china_thread_users ORDER BY id');res.json(q.rows)});
app.post('/api/users', auth, adminOnly, async (req,res)=>{const {username,display_name,role,password}=req.body;if(!username||!password||!display_name)return res.status(400).json({error:'請完整輸入帳號、姓名與密碼'});if(!['admin','manager','sales'].includes(role))return res.status(400).json({error:'角色錯誤'});try{const hash=await bcrypt.hash(password,12);const q=await pool.query('INSERT INTO china_thread_users(username,password_hash,display_name,role) VALUES($1,$2,$3,$4) RETURNING id,username,display_name,role,is_active',[username,hash,display_name,role]);res.status(201).json(q.rows[0])}catch(e){if(e.code==='23505')return res.status(409).json({error:'帳號已存在'});throw e}});
app.patch('/api/users/:id', auth, adminOnly, async (req,res)=>{const id=cleanInt(req.params.id);const {display_name,role,is_active,password}=req.body;const fields=[],vals=[];if(display_name!==undefined){vals.push(String(display_name));fields.push(`display_name=$${vals.length}`)}if(role!==undefined&&['admin','manager','sales'].includes(role)){vals.push(role);fields.push(`role=$${vals.length}`)}if(is_active!==undefined){vals.push(Boolean(is_active));fields.push(`is_active=$${vals.length}`)}if(password){vals.push(await bcrypt.hash(password,12));fields.push(`password_hash=$${vals.length}`)}if(!fields.length)return res.status(400).json({error:'沒有變更'});vals.push(id);const q=await pool.query(`UPDATE china_thread_users SET ${fields.join(',')} WHERE id=$${vals.length} RETURNING id,username,display_name,role,is_active`,vals);res.json(q.rows[0])});

function gradeSql(col='cumulative_cases'){ return `CASE WHEN ${col}>=1000 THEN 'S' WHEN ${col}>=500 THEN 'A' WHEN ${col}>=300 THEN 'B' WHEN ${col}>=100 THEN 'C' ELSE '未分級' END`; }
function rateSql(){ return `CASE WHEN monthly_target>0 THEN ROUND(monthly_actual::numeric/monthly_target*100,1) ELSE 0 END`; }
function alertSql(){ return `CASE WHEN binding_status='流失' THEN '紅' WHEN monthly_target=0 THEN '黃' WHEN monthly_actual::numeric/monthly_target>=0.85 THEN '綠' WHEN monthly_actual::numeric/monthly_target>=0.60 THEN '黃' ELSE '紅' END`; }

app.get('/api/doctors', auth, async (req,res)=>{const search=String(req.query.search||'');const q=await pool.query(`SELECT *, ${gradeSql()} AS grade, ${rateSql()} AS achievement_rate, ${alertSql()} AS alert FROM china_thread_doctors WHERE ($1='' OR name ILIKE '%'||$1||'%' OR province ILIKE '%'||$1||'%' OR city ILIKE '%'||$1||'%' OR institution ILIKE '%'||$1||'%' OR owner ILIKE '%'||$1||'%') ORDER BY updated_at DESC`,[search]);res.json(q.rows)});
app.post('/api/doctors', auth, async (req,res)=>{const d=normalized(req.body,'doctor');if(!d.name)return res.status(400).json({error:'醫師姓名必填'});const cols=Object.keys(d), vals=Object.values(d);vals.push(req.session.user.id, req.session.user.id);const params=vals.map((_,i)=>`$${i+1}`);const q=await pool.query(`INSERT INTO china_thread_doctors(${cols.join(',')},created_by,updated_by) VALUES(${params.join(',')}) RETURNING id`,vals);await log(req,'create','doctor',q.rows[0].id,{name:d.name});res.status(201).json({id:q.rows[0].id})});
app.put('/api/doctors/:id', auth, async (req,res)=>{const id=cleanInt(req.params.id),d=normalized(req.body,'doctor');if(!d.name)return res.status(400).json({error:'醫師姓名必填'});const cols=Object.keys(d),vals=Object.values(d);const sets=cols.map((c,i)=>`${c}=$${i+1}`);vals.push(req.session.user.id,id);const q=await pool.query(`UPDATE china_thread_doctors SET ${sets.join(',')},updated_by=$${vals.length-1},updated_at=NOW() WHERE id=$${vals.length} RETURNING id`,vals);if(!q.rowCount)return res.status(404).json({error:'找不到資料'});await log(req,'update','doctor',id,{name:d.name});res.json({ok:true})});

app.get('/api/institutions', auth, async (req,res)=>{const search=String(req.query.search||'');const q=await pool.query(`SELECT *, ${gradeSql()} AS grade, ${rateSql()} AS achievement_rate, ${alertSql()} AS alert FROM china_thread_institutions WHERE ($1='' OR name ILIKE '%'||$1||'%' OR province ILIKE '%'||$1||'%' OR city ILIKE '%'||$1||'%' OR owner ILIKE '%'||$1||'%' OR contact_name ILIKE '%'||$1||'%') ORDER BY updated_at DESC`,[search]);res.json(q.rows)});
app.post('/api/institutions', auth, async (req,res)=>{const d=normalized(req.body,'institution');if(!d.name)return res.status(400).json({error:'機構名稱必填'});const cols=Object.keys(d),vals=Object.values(d);vals.push(req.session.user.id,req.session.user.id);const params=vals.map((_,i)=>`$${i+1}`);const q=await pool.query(`INSERT INTO china_thread_institutions(${cols.join(',')},created_by,updated_by) VALUES(${params.join(',')}) RETURNING id`,vals);await log(req,'create','institution',q.rows[0].id,{name:d.name});res.status(201).json({id:q.rows[0].id})});
app.put('/api/institutions/:id', auth, async (req,res)=>{const id=cleanInt(req.params.id),d=normalized(req.body,'institution');if(!d.name)return res.status(400).json({error:'機構名稱必填'});const cols=Object.keys(d),vals=Object.values(d);const sets=cols.map((c,i)=>`${c}=$${i+1}`);vals.push(req.session.user.id,id);const q=await pool.query(`UPDATE china_thread_institutions SET ${sets.join(',')},updated_by=$${vals.length-1},updated_at=NOW() WHERE id=$${vals.length} RETURNING id`,vals);if(!q.rowCount)return res.status(404).json({error:'找不到資料'});await log(req,'update','institution',id,{name:d.name});res.json({ok:true})});

app.get('/api/dashboard', auth, async (_req,res)=>{
  const [kpis,statusesQ,gradesQ,alertsQ,provinceQ,cityQ,salesQ,doctorTopQ,instTopQ] = await Promise.all([
    pool.query(`WITH allx AS (SELECT binding_status,binding_date,lost_date,monthly_target,monthly_actual FROM china_thread_doctors UNION ALL SELECT binding_status,binding_date,lost_date,monthly_target,monthly_actual FROM china_thread_institutions) SELECT (SELECT COUNT(*) FROM china_thread_doctors WHERE binding_status<>'流失')::int doctors,(SELECT COUNT(*) FROM china_thread_institutions WHERE binding_status<>'流失')::int institutions,COUNT(*) FILTER(WHERE binding_date>=date_trunc('month',CURRENT_DATE) AND binding_status<>'流失')::int new_bindings,COUNT(*) FILTER(WHERE (lost_date>=date_trunc('month',CURRENT_DATE)) OR (binding_status='流失' AND lost_date IS NULL))::int lost_count,COALESCE(ROUND(AVG(CASE WHEN monthly_target>0 THEN monthly_actual::numeric/monthly_target*100 END),1),0) avg_achievement FROM allx`),
    pool.query(`SELECT binding_status label,COUNT(*)::int value FROM (SELECT binding_status FROM china_thread_doctors UNION ALL SELECT binding_status FROM china_thread_institutions)t GROUP BY binding_status ORDER BY value DESC`),
    pool.query(`SELECT grade label,COUNT(*)::int value FROM (SELECT ${gradeSql()} grade FROM china_thread_doctors UNION ALL SELECT ${gradeSql()} grade FROM china_thread_institutions)t GROUP BY grade ORDER BY CASE grade WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 WHEN 'C' THEN 4 ELSE 5 END`),
    pool.query(`SELECT alert label,COUNT(*)::int value FROM (SELECT ${alertSql()} alert FROM china_thread_doctors UNION ALL SELECT ${alertSql()} alert FROM china_thread_institutions)t GROUP BY alert`),
    pool.query(`SELECT COALESCE(province,'未設定') label,SUM(monthly_actual)::int value FROM (SELECT province,monthly_actual FROM china_thread_doctors UNION ALL SELECT province,monthly_actual FROM china_thread_institutions)t GROUP BY province ORDER BY value DESC LIMIT 10`),
    pool.query(`SELECT COALESCE(city,'未設定') label,SUM(monthly_actual)::int value FROM (SELECT city,monthly_actual FROM china_thread_doctors UNION ALL SELECT city,monthly_actual FROM china_thread_institutions)t GROUP BY city ORDER BY value DESC LIMIT 10`),
    pool.query(`SELECT COALESCE(owner,'未設定') label,SUM(monthly_actual)::int value FROM (SELECT owner,monthly_actual FROM china_thread_doctors UNION ALL SELECT owner,monthly_actual FROM china_thread_institutions)t GROUP BY owner ORDER BY value DESC LIMIT 10`),
    pool.query(`SELECT id,name,cumulative_cases,${gradeSql()} grade,monthly_actual FROM china_thread_doctors ORDER BY cumulative_cases DESC LIMIT 10`),
    pool.query(`SELECT id,name,cumulative_cases,${gradeSql()} grade,monthly_actual FROM china_thread_institutions ORDER BY cumulative_cases DESC LIMIT 10`)
  ]);
  res.json({kpis:kpis.rows[0],statuses:statusesQ.rows,grades:gradesQ.rows,alerts:alertsQ.rows,province:provinceQ.rows,city:cityQ.rows,sales:salesQ.rows,doctorTop:doctorTopQ.rows,institutionTop:instTopQ.rows});
});

app.use(express.static(path.join(__dirname,'public')));
app.get('*', (_req,res)=>res.sendFile(path.join(__dirname,'public','index.html')));

initDb().then(()=>app.listen(PORT,'0.0.0.0',()=>console.log(`Server running on ${PORT}`))).catch(err=>{console.error(err);process.exit(1)});
