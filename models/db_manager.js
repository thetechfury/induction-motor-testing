// Initialize Sequelize with SQLite database
const Sequelize = require("sequelize");

// Connect to SQLite database
const database_sequelize = new Sequelize({
    dialect: 'sqlite',  // The type of database you are using
    storage: 'databases/database.sqlite' // Provide the path where you want to store your SQLite database file
});

database_sequelize.authenticate().then(() => {
    console.log('Database Name: "database.sqlite" connection has been established successfully.');
}).catch((error) => {
    console.error('Unable to connect to the database: ', error);
});


// Export the Sequelize instance
module.exports = database_sequelize
