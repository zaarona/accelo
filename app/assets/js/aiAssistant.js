let aiAssistant = {
    init: function(){
        $("#send-message").click(function(){
            eventManager.showLoading();
            let project_name = $("#active-project-name").val();
            let version_name = $("#active-version-name").val();
            let instructions = $("#ai-assistant-input").text();
            // send instructions to backend: 
            $.ajax({
                url: "/segmentation/" + project_name + "/" + version_name + "/ai-assistant",
                type: "POST",
                data: JSON.stringify({instructions: instructions}),
                contentType: "application/json",
                success: function(response){
                    eventManager.hideLoading();
                    console.log(response);
                }
            });
        });
    }
}