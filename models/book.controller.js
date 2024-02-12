const database_sequelize = require('./db_manager.js');
const BookModel = require('./book.model.js');

database_sequelize.sync().then(() => {
    // uncomment each code block as per your requirement
    // BookModel.create({
    //     title: "My Book",
    //     author: "Ahsan Yaseen",
    //     release_date: "2024-02-08",
    //     subject: 2
    // }).then(res => {
    //     console.log(res)
    // }).catch((error) => {
    //     console.error('Failed to create a new record : ', error);
    // });

    BookModel.findAll().then(res => {
        console.log(res)
    }).catch((error) => {
        console.error('Failed to retrieve data : ', error);
    });

    // BookModel.findOne({
    //     where: {
    //         id : "2"
    //     }
    // }).then(res => {
    //     console.log(res)
    // }).catch((error) => {
    //     console.error('Failed to retrieve data : ', error);
    // });

    // BookModel.destroy({
    //     where: {
    //         id: 3
    //     }
    // }).then(() => {
    //     console.log("Successfully deleted record.")
    // }).catch((error) => {
    //     console.error('Failed to delete record : ', error);
    // });

    // BookModel.findOne({where: {id: 2}})
    //     .then(book => {
    //         if (book) {
    //             // Record exists, so delete it
    //             Book.destroy({where: {id: 2}})
    //             return console.log("Successfully deleted record.")
    //         } else {
    //             // Record does not exist, so log an error message
    //             console.error("Record with id 3 does not exist.");
    //         }
    //     })
    //     .catch((error) => {
    //         console.error('Failed to delete record : ', error);
    //     });

})
