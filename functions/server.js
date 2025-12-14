require('dotenv').config();
const express = require('express');
const path = require('path');
const nodemailer = require('nodemailer');
const fs = require('fs'); // File System module for View Counter
const app = express();

const PORT = process.env.PORT || 5000;
const BASE_DIR = path.resolve(__dirname, '..');
const VIEWS_FILE = path.join(BASE_DIR, 'views.json');

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use('/static', express.static(path.join(BASE_DIR, 'static')));

// --- VIEW COUNTER LOGIC ---
let viewData = { count: 0, ips: [] };

// Load views from file on startup
if (fs.existsSync(VIEWS_FILE)) {
    try {
        const data = fs.readFileSync(VIEWS_FILE, 'utf8');
        viewData = JSON.parse(data);
    } catch (err) {
        console.error("Error reading views file, starting fresh.");
    }
}

// Function to save views
const saveViews = () => {
    fs.writeFileSync(VIEWS_FILE, JSON.stringify(viewData, null, 2));
};

// Middleware to track unique visits
const trackViews = (req, res, next) => {
    // Get IP (handles proxies like Nginx/Heroku if you deploy later)
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    
    if (!viewData.ips.includes(ip)) {
        viewData.ips.push(ip);
        viewData.count++;
        saveViews();
        console.log(`New Visitor! Unique IP: ${ip}. Total Views: ${viewData.count}`);
    }
    next();
};

// --- ROUTES ---

// Apply tracking only to the home page
app.get('/', trackViews, (req, res) => {
    res.sendFile(path.join(BASE_DIR, 'templates', 'index.html'));
});

// Endpoint to get view count (Optional: if you want to show it on frontend)
app.get('/api/views', (req, res) => {
    res.json({ count: viewData.count });
});

app.get('/projects', (req, res) => {
    res.sendFile(path.join(BASE_DIR, 'templates', 'projects.html'));
});

app.get('/achievements', (req, res) => {
    res.sendFile(path.join(BASE_DIR, 'templates', 'achievements.html'));
});

// --- EMAIL LOGIC ---
app.post('/send-email', async (req, res) => {
    const { name, email, message } = req.body;

    const transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: {
            user: process.env.GMAIL_USER,
            pass: process.env.GMAIL_APP_PASSWORD
        }
    });

    // Professional HTML Email Template
    // Note: We use an absolute URL for the logo. Ensure your logo is hosted online 
    // or use the specific Google Drive link you provided in the prompt logic.
    const logoUrl = "https://raw.githubusercontent.com/BinhPhamTieSinger/binhphamtiesinger.github.io/main/static/assets/images/logo.png"; 
    // ^ Replace this with your actual hosted image URL if the github one isn't live yet, 
    // or use the Google Drive ID method you mentioned.

    const htmlContent = `
    <div style="background-color: #0f0f0f; color: #e0e0e0; font-family: 'Poppins', sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; border-radius: 10px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <!-- Logo Section -->
            <img src="${logoUrl}" alt="TieSinger Logo" style="width: 80px; margin-bottom: 10px;">
            <h2 style="color: #5865F2; margin: 0;">New Contact Message</h2>
        </div>
        
        <div style="background-color: #1e1e1e; padding: 25px; border-radius: 8px; border-left: 4px solid #5865F2;">
            <p style="margin: 0 0 10px 0;"><strong>👤 Name:</strong> ${name}</p>
            <p style="margin: 0 0 10px 0;"><strong>📧 Email:</strong> <a href="mailto:${email}" style="color: #5865F2;">${email}</a></p>
            <div style="margin-top: 20px;">
                <strong>💬 Message:</strong>
                <p style="background-color: #2b2b2b; padding: 15px; border-radius: 5px; margin-top: 5px; line-height: 1.6;">
                    ${message.replace(/\n/g, '<br>')}
                </p>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #666;">
            <p>&copy; 2025 TieSinger Portfolio System</p>
            <p>IP Address: ${req.headers['x-forwarded-for'] || req.socket.remoteAddress}</p>
        </div>
    </div>
    `;

    const mailOptions = {
        from: `"${name}" <${email}>`,
        to: "phamquocbinh2018@gmail.com", 
        subject: `StartUp Notification: Message from ${name}`,
        html: htmlContent
    };

    try {
        await transporter.sendMail(mailOptions);
        res.status(200).json({ success: true, message: 'Email sent successfully!' });
    } catch (error) {
        console.error('Error sending email:', error);
        res.status(500).json({ success: false, message: 'Failed to send email.' });
    }
});

// app.listen(PORT, () => {
//     console.log(`Server running at http://localhost:${PORT}`);
// });

app.use("/.netlify/functions/server", router);
module.exports.handler = serverless(app);