document.getElementById('main-modal').addEventListener('show.bs.modal', function (event) {
    document.querySelector('#v-pills-home').classList.add('show', 'active');
    document.querySelector('#motor_identification').classList.add('active');
    document.querySelector('#v-pills-profile').classList.remove('show', 'active');
    document.querySelector('#performed_tests').classList.remove('active');


    document.getElementById("id_form-0-test_type").setAttribute("disabled", "");
    document.getElementById("id_form-1-test_type").setAttribute("disabled", "");
    document.getElementById("id_form-2-test_type").setAttribute("disabled", "");
    document.getElementById("id_form-3-test_type").setAttribute("disabled", "");
    document.getElementById("id_form-4-test_type").setAttribute("disabled", "");
    document.getElementById("id_form-5-test_type").setAttribute("disabled", "");
})


document.getElementById("main-form").addEventListener("submit", function (event) {
    // Flag to track if any field is empty
    var anyFieldEmpty = false;

    // Check the first input field
    var serialNumberField = document.getElementById("id_serial_number");
    var serialNumberErrorMessage = serialNumberField.nextElementSibling;
    if (serialNumberField.value.trim() === "") {
        serialNumberErrorMessage.style.display = "block";
        anyFieldEmpty = true;
    } else {
        serialNumberErrorMessage.style.display = "none";
    }

    // Check the second input field
    var customerNameField = document.getElementById("id_customer_name");
    var customerNameErrorMessage = customerNameField.nextElementSibling;
    if (customerNameField.value.trim() === "") {
        customerNameErrorMessage.style.display = "block";
        anyFieldEmpty = true;
    } else {
        customerNameErrorMessage.style.display = "none";
    }

    // Check the third input field
    var salesOrderNumberField = document.getElementById("id_sales_order_number");
    var salesOrderNumberErrorMessage = salesOrderNumberField.nextElementSibling;
    if (salesOrderNumberField.value.trim() === "") {
        salesOrderNumberErrorMessage.style.display = "block";
        anyFieldEmpty = true;
    } else {
        salesOrderNumberErrorMessage.style.display = "none";
    }

    // If any field is empty, prevent form submission
    if (anyFieldEmpty) {
        event.preventDefault();
    }

    var checkboxes = document.querySelectorAll('input[type="checkbox"]');
    var atLeastOneChecked = false;

    for (let i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked) {
            atLeastOneChecked = true;
            break;
        }
    }

    if (!atLeastOneChecked) {
        document.getElementById("error-message").style.display = "block";
        document.querySelector('#v-pills-home').classList.remove('show', 'active');
        document.querySelector('#motor_identification').classList.remove('active');
        document.querySelector('#v-pills-profile').classList.add('show', 'active');
        document.querySelector('#performed_tests').classList.add('active');
        event.preventDefault(); // Prevent form submission
    } else {
        document.getElementById("error-message").style.display = "none";
    }

    if (!anyFieldEmpty && atLeastOneChecked) {
        document.getElementById("id_form-0-test_type").removeAttribute("disabled");
        document.getElementById("id_form-1-test_type").removeAttribute("disabled");
        document.getElementById("id_form-2-test_type").removeAttribute("disabled");
        document.getElementById("id_form-3-test_type").removeAttribute("disabled");
        document.getElementById("id_form-4-test_type").removeAttribute("disabled");
        document.getElementById("id_form-5-test_type").removeAttribute("disabled");

        var myModal = document.getElementById('main-modal');
        var modal = bootstrap.Modal.getInstance(myModal);
        modal.hide();
    }
});

document.getElementById('main-modal').addEventListener('hidden.bs.modal', function (event) {
    document.getElementById("main-form").reset();
    // Display None for error messages
    document.getElementById("id_serial_number").nextElementSibling.style.display = "none";
    document.getElementById("id_customer_name").nextElementSibling.style.display = "none";
    document.getElementById("id_sales_order_number").nextElementSibling.style.display = "none";
    document.getElementById("error-message").style.display = "none";
})

function deleteRecord(deletedRowID) {
    var result = confirm(" Want to delete ID: " + deletedRowID);
    if (result) {
        $.get("/report/" + deletedRowID + "/delete", function () {
        })
            .done(function () {
                alert("Successfuly Deleted");
                location.reload();
            })
            .fail(function () {
                alert("error");
            });
    }
}