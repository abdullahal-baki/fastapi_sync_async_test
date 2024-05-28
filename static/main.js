
function test(){

    console.log("Testing_");
}
test();
document.addEventListener("DOMContentLoaded", function() {
    const asyncForm = document.getElementById("async-form");
    const submitButton = document.getElementById("submit-async");
    const asyncResult = document.getElementById("async-result");

    submitButton.onclick = function() {
        console.log("Function called");
        var formData = new FormData(asyncForm);
        
        // Log the form data for debugging purposes
        for (var pair of formData.entries()) {
            console.log(pair[0] + ': ' + pair[1]);
        }
        console.log(addMessageAsyncUrl);
        fetch(addMessageAsyncUrl, {
            method: "POST",
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(data); 
            if (data.message) {
                asyncResult.innerHTML = data.message;
            } else if (data.errors) {
                let errorMessages = '';
                for (let field in data.errors) {
                    data.errors[field].forEach(error => {
                        errorMessages += `<span style="color: red;">${error}</span><br>`;
                    });
                }
                asyncResult.innerHTML = errorMessages;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            asyncResult.innerHTML = "There was an error processing your request.";
        });
    };
});
