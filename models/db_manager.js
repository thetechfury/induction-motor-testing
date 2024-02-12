// Initialize Sequelize with SQLite database
const Sequelize = require("sequelize");

const database_sequelize = new Sequelize({
    dialect: 'sqlite',
    storage: 'databases/database.sqlite' // Provide the path where you want to store your SQLite database file
});

database_sequelize.authenticate().then(() => {
    console.log('Connection has been established successfully.');
}).catch((error) => {
    console.error('Unable to connect to the database: ', error);
});

module.exports = database_sequelize
