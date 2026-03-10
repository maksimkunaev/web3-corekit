// simulate_webhook.js
// Utility to simulate NowPayments IPN webhooks for local testing.
// Requries: npm install axios dotenv
const crypto = require("crypto");
const axios = require("axios");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, "../backend/.env") });

const IPN_SECRET = process.env.NOWPAYMENTS_IPN_SECRET || "your_ipn_secret_here";
const API_URL = process.env.DOMAIN_URL
    ? `${process.env.DOMAIN_URL}/api/crypto/webhook`
    : "http://127.0.0.1:9000/api/crypto/webhook";

// Example wallet and plan
const WALLET = process.env.TEST_USER_WALLET_ADDRESS;
const PLAN_ID = "pro";

const webhooks = [
    {
        payment_id: 123456789,
        payment_status: "finished",
        pay_address: "0x...",
        price_amount: 9.99,
        price_currency: "usd",
        pay_amount: 10.0,
        pay_currency: "usdttrc20",
        order_id: `${WALLET}|${PLAN_ID}|${Date.now()}`,
        order_description: "Pro Plan Subscription",
        created_at: new Date().toISOString(),
        updated_at: Date.now(),
    },
];

function sortObject(obj) {
    return Object.keys(obj)
        .sort()
        .reduce((result, key) => {
            result[key] =
                obj[key] && typeof obj[key] === "object"
                    ? sortObject(obj[key])
                    : obj[key];
            return result;
        }, {});
}

async function sendWebhook(payload, index) {
    // NowPayments IPN signature is calculated on sorted JSON
    const sortedPayload = sortObject(payload);
    const jsonString = JSON.stringify(sortedPayload);

    const hmac = crypto.createHmac("sha512", IPN_SECRET);
    hmac.update(jsonString);
    const signature = hmac.digest("hex");

    console.log("\n" + "=".repeat(60));
    console.log(`[${index + 1}/${webhooks.length}] Sending: ${payload.payment_status}`);
    console.log("=".repeat(60));
    console.log(`Target: ${API_URL}`);
    console.log(`Order:  ${payload.order_id}`);
    console.log(`Signature: ${signature}`);

    try {
        const response = await axios.post(API_URL, jsonString, {
            headers: {
                "Content-Type": "application/json",
                "x-nowpayments-sig": signature,
            },
        });

        console.log(`Status: ${response.status}`);
        console.log(`✅ SUCCESS: ${JSON.stringify(response.data)}`);
    } catch (error) {
        console.log(`Status: ${error.response?.status || "ERROR"}`);
        console.log(`❌ FAILED: ${JSON.stringify(error.response?.data) || error.message}`);
    }
}

async function runTests() {
    console.log("Starting Webhook Simulation...");
    for (let i = 0; i < webhooks.length; i++) {
        await sendWebhook(webhooks[i], i);
        if (i < webhooks.length - 1) {
            await new Promise((resolve) => setTimeout(resolve, 1000));
        }
    }
}

runTests();
