
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