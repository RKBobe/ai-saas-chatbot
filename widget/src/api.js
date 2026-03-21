const API_URL = "http://localhost:8000/api/v1/chat";

export const sendMessage = async (message, clientId = "demo-client") => {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message,
                client_id: clientId,
                user_id: "widget-user-" + Math.random().toString(36).substr(2, 9),
            }),
        });

        if (!response.ok) {
            throw new Error("Network response was not ok");
        }

        const data = await response.json();
        return data.reply;
    } catch (error) {
        console.error("Chat API Error:", error);
        return "I'm having trouble connecting to the server.";
    }
};
