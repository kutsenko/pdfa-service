// MongoDB initialization script for PDF/A Service
// This script creates the application user with limited permissions
// and sets up the initial database structure with indexes

const dbName = process.env.MONGO_INITDB_DATABASE || 'pdfa_service';
const dbUser = process.env.PDFA_DB_USER || 'pdfa_user';
const dbPassword = process.env.PDFA_DB_PASSWORD || 'change_this_password';

print('=== MongoDB Initialization for PDF/A Service ===');
print(`Database: ${dbName}`);
print(`User: ${dbUser}`);

// Switch to admin database to create user
db = db.getSiblingDB('admin');

// Create application user with readWrite permissions on pdfa_service database
db.createUser({
  user: dbUser,
  pwd: dbPassword,
  roles: [
    {
      role: 'readWrite',
      db: dbName
    }
  ]
});

print(`✓ Created user '${dbUser}' with readWrite permissions on '${dbName}'`);

// Switch to application database
db = db.getSiblingDB(dbName);

// Create collections
print('\nCreating collections...');
db.createCollection('users');
db.createCollection('jobs');
db.createCollection('oauth_states');
db.createCollection('audit_logs');
print('✓ Collections created: users, jobs, oauth_states, audit_logs');

// Create indexes for users collection
print('\nCreating indexes for users collection...');
db.users.createIndex({user_id: 1}, {unique: true, name: 'idx_user_id'});
db.users.createIndex({email: 1}, {name: 'idx_email'});
db.users.createIndex({last_login_at: -1, login_count: -1}, {name: 'idx_login_stats'});
print('✓ Users indexes: user_id (unique), email, login_stats');

// Create indexes for jobs collection
print('\nCreating indexes for jobs collection...');
db.jobs.createIndex({job_id: 1}, {unique: true, name: 'idx_job_id'});
db.jobs.createIndex({user_id: 1, created_at: -1}, {name: 'idx_user_jobs'});
db.jobs.createIndex({status: 1, created_at: -1}, {name: 'idx_status_created'});
db.jobs.createIndex({status: 1, completed_at: -1, duration_seconds: 1}, {name: 'idx_analytics'});

// TTL index: Jobs automatically deleted after 90 days (7776000 seconds)
db.jobs.createIndex(
  {created_at: 1},
  {expireAfterSeconds: 7776000, name: 'idx_ttl_90days'}
);
print('✓ Jobs indexes: job_id (unique), user_jobs, status, analytics');
print('✓ Jobs TTL: 90 days (auto-cleanup)');

// Create indexes for oauth_states collection
print('\nCreating indexes for oauth_states collection...');
db.oauth_states.createIndex({state: 1}, {unique: true, name: 'idx_state'});

// TTL index: OAuth states automatically deleted after 10 minutes (600 seconds)
db.oauth_states.createIndex(
  {created_at: 1},
  {expireAfterSeconds: 600, name: 'idx_ttl_10min'}
);
print('✓ OAuth states indexes: state (unique)');
print('✓ OAuth states TTL: 10 minutes (auto-cleanup)');

// Create indexes for audit_logs collection
print('\nCreating indexes for audit_logs collection...');
db.audit_logs.createIndex({user_id: 1, timestamp: -1}, {name: 'idx_user_audit'});
db.audit_logs.createIndex({event_type: 1, timestamp: -1}, {name: 'idx_event_type'});
db.audit_logs.createIndex({event_type: 1, ip_address: 1, timestamp: -1}, {name: 'idx_security'});

// TTL index: Audit logs automatically deleted after 1 year (31536000 seconds)
db.audit_logs.createIndex(
  {timestamp: 1},
  {expireAfterSeconds: 31536000, name: 'idx_ttl_1year'}
);
print('✓ Audit logs indexes: user_audit, event_type, security');
print('✓ Audit logs TTL: 1 year (auto-cleanup)');

print('\n=== MongoDB Initialization Complete ===');
print(`\nSummary:`);
print(`  - Database: ${dbName}`);
print(`  - User: ${dbUser} (readWrite)`);
print(`  - Collections: 4 (users, jobs, oauth_states, audit_logs)`);
print(`  - Indexes: 14 total`);
print(`  - TTL policies: Jobs (90d), OAuth (10m), Audit (1y)`);
print('\nDatabase is ready for use.');
