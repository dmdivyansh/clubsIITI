


$(document).ready(function () {

    //Remove the navbar toggle button 
    $(".navbar-toggler").remove()

    //Remove the contact portion
    $("#contact").remove()

    //Remove the about portion
    $("#about").remove()

    //Add space below the submit button
    $("button").addClass("mb-5");


    // VALIDATING ROLL NO FIELD AND PUTTING THE EXPECTED VALUES
    $("#roll_no").focusout(function () {

        var branch = this.value.toString()[5];

        if (branch == 1) {
            $("#branch").val("CSE");
            $("#mail_id").val("cse" + $("#roll_no").val() + "@iiti.ac.in")
        }

        else if (branch == 2) {
            $("#branch").val("EE");
            $("#mail_id").val("ee" + $("#roll_no").val() + "@iiti.ac.in")

        }

        else if (branch == 3) {
            $("#branch").val("ME");
            $("#mail_id").val("me" + $("#roll_no").val() + "@iiti.ac.in")

        }

        else if (branch == 4) {
            $("#branch").val("CE");
            $("#mail_id").val("ce" + $("#roll_no").val() + "@iiti.ac.in")

        }

        else if (branch == 5) {
            $("#branch").val("MEMS");
            $("#mail_id").val("mems" + $("#roll_no").val() + "@iiti.ac.in")

        }

        else {
            alert("Invalid Roll No.")
            $("#roll_no").val("");
            $("#roll_no").focus();
        }

    });
});