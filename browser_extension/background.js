chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "sendToWebhook") {
      
      // ⚠️ REPLACE THIS WITH YOUR ACTUAL WEBHOOK URL
      const WEBHOOK_URL = "http://127.0.0.1:8000/webhook";  
      // Prepare the payload
      const payload = {
        sourceUrl: sender.tab ? sender.tab.url : "Unknown URL",
        title: sender.tab ? sender.tab.title : "Unknown Title",
        timestamp: new Date().toISOString(),
        html: request.data
      };
  
      // Send the data to the webhook
      fetch(WEBHOOK_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      })
      .then(response => {
        if (response.ok) {
          console.log("Successfully sent HTML to webhook!");
        } else {
          console.error("Webhook responded with an error:", response.status);
        }
      })
      .catch(error => {
        console.error("Network error while sending to webhook:", error);
      });
    }
    
    // Required to keep the message channel open for async responses if needed
    return true; 
  });