const {DataTypes} = require("sequelize");

const database_sequelize = require('./db_manager.js');

// Define a model for the 'books' table
const BookModel = database_sequelize.define("books", {
    title: {
        type: DataTypes.STRING,
        allowNull: false
    },
    author: {
        type: DataTypes.STRING,
        allowNull: false
    },
    release_date: {
        type: DataTypes.DATEONLY,
    },
    subject: {
        type: DataTypes.INTEGER,
    }
});

// database_sequelize.sync().then(() => {
//    console.log('Book table created successfully!');
// }).catch((error) => {
//    console.error('Unable to create table : ', error);
// });

// Export the Book model
module.exports = BookModel
