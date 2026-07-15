const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
db.run(
  "update workflow_entity set active = 0 where id = '1bb14df7-9ae1-4224-b546-aee563e38d0c'",
  (err) => {
    if (err) {
      console.error(err);
      process.exit(1);
    }
    console.log('WF3 deactivated');
    db.close();
  },
);
