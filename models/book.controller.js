// const database_sequelize = require('./db_manager.js');
const BookModel = require('./book.model.js');

// database_sequelize.sync().then(() => {
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

    // BookModel.findAll().then(res => {
    //     console.log(res)
    // }).catch((error) => {
    //     console.error('Failed to retrieve data : ', error);
    // });

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

// })

// for creating a new book instance/record
// Controller for creating a new book
exports.createBook = async (req, res) => {
  try {
    const { title, author, release_date, subject } = req.body;
    const book = await BookModel.create({ title, author, release_date, subject });
    res.json({ message: 'Book created successfully', book });
  } catch (error) {
    console.error(error);
    res.status(500).send('Internal Server Error');
  }
};

// getting all books records
exports.getAllBooks = async (req, res) => {
  try {
    const books = await BookModel.findAll();
    res.json(books);
  } catch (error) {
    console.error(error);
    res.status(500).send('Internal Server Error');
  }
};

// Controller for getting a book by ID
exports.getBookById = async (req, res) => {
  try {
    const bookId = req.params.id;
    const book = await BookModel.findByPk(bookId);
    if (!book) {
      res.status(404).send('Book not found');
    } else {
      res.json(book);
    }
  } catch (error) {
    console.error(error);
    res.status(500).send('Internal Server Error');
  }
};

