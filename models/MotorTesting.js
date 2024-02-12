// const sqlite = require('sqlite3').verbose()
// const db = new sqlite.Database('./databases/database.db', sqlite.OPEN_READWRITE, (err)=>{
//     if (err) return console.log(err)
// })
//
// const sql = `CREATE TABLE MotorTesting(id INTEGER PRIMARY KEY, name)`
// db.run(sql)

// models/MotorTesting.js

const DataTypes = require('sequelize');
// const sequelize = new Sequelize('sqlite::memory:');
const sequelize = require('./index.js');

const MotorTesting = sequelize.define('MotorTesting', {
    // Model attributes are defined here
    id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        allowNull: false,
        primaryKey: true
    },
    name: {
        type: DataTypes.STRING,
        allowNull: false
    }
}, {
    // Other model options go here
});


const MotorNumbers = sequelize.define('MotorNumbers', {
    // Model attributes are defined here
    id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        allowNull: false,
        primaryKey: true
    },
    motor_number: {
        type: DataTypes.INTEGER,
        allowNull: false
    },
    motor_name: {
        type: DataTypes.STRING,
        allowNull: false
    }
}, {
    // Other model options go here
});

module.exports = MotorNumbers
module.exports = MotorTesting


// `sequelize.define` also returns the model
// console.log(MotorTesting === sequelize.models.MotorTesting); // true
//
// try {
//   sequelize.authenticate();
//   console.log('Connection has been established successfully.');
// } catch (error) {
//   console.error('Unable to connect to the database:', error);
// }
