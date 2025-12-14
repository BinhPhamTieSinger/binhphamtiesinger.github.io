# 🎨 TieSinger Portfolio Website

A stunning personal portfolio website featuring **Neon (Blue + Purple)** theme with **Neumorphism** design. Built with Node.js (Express) backend and modern HTML/CSS/JS frontend.

## ✨ Features

### 🏠 **Home Page**
- **Animated Intro Sequence**: Logo animation → Greeting → Main content
- **Hero Section**: Typing effect with multiple phrases
- **About Section**: Beautiful neumorphism card with profile image
- **Contact Form**: Integrated with Nodemailer for email notifications
- **Sticky Header**: Transforms when user scrolls

### 📂 **Projects Page**
- **Project Cards**: Neon-styled cards with hover effects
- **Modal Popups**: Detailed project descriptions
- **5 Featured Projects**:
  1. ML & DL Learning Platform
  2. Geometry Problem Parser
  3. AI Agent Chatbot System
  4. ThetaMind Math Platform
  5. Unity Game Development

### 🏆 **Achievements Page**
- **PDF Viewer**: Upload and view CV/Resume
- **Navigation Controls**: Page navigation, zoom in/out
- **PDF.js Integration**: Client-side PDF rendering

### 📊 **Analytics**
- **IP Counter**: Tracks unique visitors
- **View Counter**: Displays total page views
- **Data Persistence**: Saves to `views.json`

## 🚀 Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation

1. **Clone the repository**:
```bash
cd D:\Development\Web_Development\binhphamtiesinger.github.io
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure Environment Variables**:
Create a `.env` file in the root directory:
```env
PORT=3000
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

**How to get Gmail App Password:**
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Go to "App passwords"
4. Generate password for "Mail"
5. Copy the 16-character password to `.env`

4. **Add Your Images**:
Place these images in `static/assets/images/`:
- `logo.png` - Your logo
- `avatar.png` - Avatar for intro greeting
- `aboutme.png` - Profile image for About section
- `contact.png` - Contact section image

### Running the Server

**Development**:
```bash
npm start
```

Visit: `http://localhost:3000`

**Production** (Deploy to services like Heroku, Vercel, Railway):
```bash
node server.js
```

## 📁 Project Structure

```
binhphamtiesinger.github.io/
│
├── static/
│   ├── assets/
│   │   └── images/
│   │       ├── logo.png
│   │       ├── avatar.png
│   │       ├── aboutme.png
│   │       └── contact.png
│   ├── css/
│   │   ├── style.css          # Main styles (Neon + Neumorphism)
│   │   └── projects.css       # Projects page styles
│   └── js/
│       ├── main.js            # Home page logic
│       └── projects.js        # Projects page logic
│
├── templates/
│   ├── index.html             # Home page
│   ├── projects.html          # Projects page
│   └── achievements.html      # Achievements page
│
├── server.js                  # Express server
├── views.json                 # IP counter data
├── package.json
├── .env                       # Environment variables (create this)
└── README.md
```

## 🎨 Design System

### Color Palette
```css
--neon-blue: #5865F2
--neon-purple: #9B59B6
--neon-cyan: #00D9FF
--dark-bg: #0a0a0f
--dark-surface: #151520
--dark-elevated: #1e1e2e
```

### Neumorphism Shadows
```css
/* Light surfaces */
box-shadow: 
    20px 20px 60px #c8c8c8,
    -20px -20px 60px #ffffff;

/* Dark surfaces */
box-shadow: 
    10px 10px 30px rgba(0, 0, 0, 0.7),
    -10px -10px 30px rgba(255, 255, 255, 0.02);
```

### Neon Glow Effects
```css
box-shadow: 0 0 30px rgba(88, 101, 242, 0.5);
text-shadow: 0 0 20px rgba(88, 101, 242, 0.5);
```

## 🛠️ Customization Guide

### 1. Update Personal Information

**In `templates/index.html`**:
- Change name: "TieSinger" → Your Name
- Update social media links (currently placeholders: FB, DC, X)
- Modify About Me text

**In `server.js`**:
- Change recipient email in `mailOptions.to`
- Update logo URL for email template

### 2. Add Your Projects

**In `static/js/projects.js`**:
Edit the `projectsData` object with your projects:
```javascript
'your-project-id': {
    title: 'Your Project Name',
    icon: '🎯', // Emoji icon
    description: `
        <p>Your description...</p>
        <h3>Key Features:</h3>
        <ul>
            <li>Feature 1</li>
        </ul>
    `,
    link: 'https://your-project.com'
}
```

**In `templates/projects.html`**:
Add corresponding project cards in the grid.

### 3. Customize Colors

**In `static/css/style.css`** and `static/css/projects.css`**:
Modify the `:root` variables:
```css
:root {
    --neon-blue: #YOUR_COLOR;
    --neon-purple: #YOUR_COLOR;
    /* ... */
}
```

### 4. Change Typing Effect Text

**In `static/js/main.js`**:
```javascript
const words = [
    "Your first phrase.",
    "Your second phrase."
];
```

## 📧 Contact Form Setup

The contact form sends formatted emails with:
- ✅ Beautiful HTML template
- ✅ Sender's name and email
- ✅ Message content
- ✅ IP address tracking
- ✅ Logo in email header

Make sure to set up your Gmail credentials in `.env`.

## 🔒 Security Notes

1. **Never commit `.env` to Git**:
```bash
echo ".env" >> .gitignore
```

2. **Use App Passwords** (not your actual Gmail password)

3. **Rate Limiting**: Consider adding rate limiting for production:
```bash
npm install express-rate-limit
```

## 📱 Responsive Design

The website is fully responsive with breakpoints at:
- **Desktop**: 1024px+
- **Tablet**: 768px - 1024px
- **Mobile**: < 768px

All sections adapt gracefully to different screen sizes.

## 🚀 Deployment

### Deploy to Heroku
```bash
heroku create your-app-name
git push heroku main
heroku config:set GMAIL_USER=your-email@gmail.com
heroku config:set GMAIL_APP_PASSWORD=your-app-password
```

### Deploy to Vercel
```bash
vercel --prod
```

### Deploy to Railway
```bash
railway up
```

## 📊 View Counter

The view counter tracks:
- **Unique IPs**: Each unique visitor is counted once
- **Total Views**: Stored in `views.json`
- **API Endpoint**: `GET /api/views` returns `{ count: number }`

## 🎯 Future Enhancements

- [ ] Add dark/light mode toggle
- [ ] Blog section with markdown support
- [ ] Admin dashboard for view statistics
- [ ] Contact form with reCAPTCHA
- [ ] Project search/filter functionality
- [ ] Downloadable CV from Achievements page
- [ ] Social media share buttons
- [ ] Animation preloader

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

Feel free to fork this project and customize it for your own portfolio!

## 💬 Support

If you have any questions or need help setting up, feel free to reach out:
- Email: phamquocbinh2018@gmail.com
- GitHub: [@TieSinger](https://github.com/BinhPhamTieSinger)

---

**Made with ❤️ by TieSinger**

*Powered by Node.js, Express, and modern web technologies*
