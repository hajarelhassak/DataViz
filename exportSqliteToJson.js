// scripts/exportSqliteToJson.js
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');

// Connexion à votre base SQLite
const db = new sqlite3.Database('./your_database.db');

// Fonction pour exporter une table
const exportTable = (tableName) => {
  return new Promise((resolve, reject) => {
    db.all(`SELECT * FROM ${tableName}`, (err, rows) => {
      if (err) reject(err);
      resolve(rows);
    });
  });
};

// Exporter toutes les tables nécessaires
const exportAllTables = async () => {
  try {
    const tables = ['products', 'users', 'orders', 'customers', 'categories'];
    
    for (const table of tables) {
      const data = await exportTable(table);
      // Sauvegarder en JSON
      fs.writeFileSync(
        `./data/${table}.json`,
        JSON.stringify(data, null, 2)
      );
      console.log(`✅ Table ${table} exportée: ${data.length} lignes`);
    }
    
    console.log('✅ Exportation terminée !');
  } catch (error) {
    console.error('❌ Erreur:', error);
  } finally {
    db.close();
  }
};

exportAllTables();