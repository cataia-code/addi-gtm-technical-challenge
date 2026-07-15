const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');

const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');
const ids = [
  '8eb94d84-fb9d-416b-9805-150c5dd5f02d',
  '94ae8bc4-5361-4845-a955-96bfbb5d7b4c'
];

db.all(
  `select workflowId, node, webhookPath, method, webhookId, pathLength
   from webhook_entity
   where workflowId in (?, ?)
   order by workflowId, method, webhookPath`,
  ids,
  (err, rows) => {
  if (err) {
    console.error(err);
    process.exit(1);
  }

  console.log(JSON.stringify(rows, null, 2));
  db.close();
  },
);
