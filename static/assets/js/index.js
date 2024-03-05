function enableTestTypeFields() {
    document.getElementById("id_form-0-test_type").removeAttribute("disabled");
    document.getElementById("id_form-1-test_type").removeAttribute("disabled");
    document.getElementById("id_form-2-test_type").removeAttribute("disabled");
    document.getElementById("id_form-3-test_type").removeAttribute("disabled");
    document.getElementById("id_form-4-test_type").removeAttribute("disabled");
    document.getElementById("id_form-5-test_type").removeAttribute("disabled");
    document.getElementById("id_form-6-test_type").removeAttribute("disabled");
}

document.getElementById('main-modal').addEventListener('show.bs.modal', function (event) {
    document.querySelector('#v-pills-home').classList.add('show', 'active');
    document.querySelector('#motor_identification').classList.add('active');
    document.querySelector('#v-pills-profile').classList.remove('show', 'active');
    document.querySelector('#performed_tests').classList.remove('active');
})

document.getElementById('edit-modal').addEventListener('show.bs.modal', function (event) {
    document.querySelector('#edit-v-pills-home').classList.add('show', 'active');
    document.querySelector('#edit_motor_identification').classList.add('active');
    document.querySelector('#edit-v-pills-profile').classList.remove('show', 'active');
    document.querySelector('#edit_performed_tests').classList.remove('active');
})

document.getElementById("main-form").addEventListener("submit", function (event) {
    var checkboxes = document.querySelectorAll('input[type="checkbox"]');
    var atLeastOneChecked = false;

    for (var i = 0; i < checkboxes.length; i++) {
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

    if (atLeastOneChecked) {
        enableTestTypeFields()
        var myModal = document.getElementById('main-modal');
        var modal = bootstrap.Modal.getInstance(myModal);
        modal.hide();
    }
});

document.getElementById("edit-form").addEventListener("submit", function (event) {
    var checkboxes = document.querySelectorAll('input[type="checkbox"]');
    var atLeastOneChecked = false;

    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked) {
            atLeastOneChecked = true;
            break;
        }
    }

    if (!atLeastOneChecked) {
        document.getElementById("edit-error-message").style.display = "block";
        document.querySelector('#edit-v-pills-home').classList.remove('show', 'active');
        document.querySelector('#edit_motor_identification').classList.remove('active');
        document.querySelector('#edit-v-pills-profile').classList.add('show', 'active');
        document.querySelector('#edit_performed_tests').classList.add('active');
        event.preventDefault(); // Prevent form submission
    } else {
        document.getElementById("edit-error-message").style.display = "none";
    }

    if (atLeastOneChecked) {
        enableTestTypeFields()
        var myModal = document.getElementById('edit-modal');
        var modal = bootstrap.Modal.getInstance(myModal);
        modal.hide();
    }
});

document.getElementById('main-modal').addEventListener('hidden.bs.modal', function (event) {
    document.getElementById("main-form").reset();
    // Display None for error messages
    document.getElementById("error-message").style.display = "none";
})

document.getElementById('edit-modal').addEventListener('hidden.bs.modal', function (event) {
    document.getElementById("edit-form").reset();
    // Display None for error messages
    document.getElementById("edit-error-message").style.display = "none";
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

// Select the first form
const firstTab = document.querySelector('#testFormTabs li:first-child');

// if (firstTab) {
//     firstTab.querySelector('button').click();
// } else {
//     console.error('The first li element was not found in the ul.');
// }
