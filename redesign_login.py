from pathlib import Path
import re
from datetime import datetime

root = Path(r"C:\COLLEG-PLACEMENT-MANAGEMENT")
index = root / "frontend" / "index.html"
css = root / "frontend" / "css" / "style.css"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Backup existing files
index_backup = index.with_name(f"index_backup_{timestamp}.html")
css_backup = css.with_name(f"style_backup_{timestamp}.css")

index_backup.write_text(index.read_text(encoding="utf-8"), encoding="utf-8")
css_backup.write_text(css.read_text(encoding="utf-8"), encoding="utf-8")

html = index.read_text(encoding="utf-8")

# Remove the old left-side welcome panel only.
html = re.sub(
    r'<section class="welcome-panel".*?</section>\s*',
    '',
    html,
    flags=re.S
)

# Add the new header/logo before the login card.
header = r'''
<header class="college-header">
    <div class="blueprint-decoration blueprint-left">LEARN<br>GROW<br>BUILD<br>YOUR FUTURE</div>

    <h1>COLLEGE PLACEMENT MANAGEMENT SYSTEM</h1>

    <div class="graduation-logo" aria-label="College graduation logo">
        <svg viewBox="0 0 260 220" role="img" aria-hidden="true">
            <path class="logo-line" d="M130 20 L215 55 L130 90 L45 55 Z"/>
            <path class="logo-line" d="M75 68 L75 105 Q130 140 185 105 L185 68"/>
            <path class="logo-line" d="M130 90 L130 145"/>
            <path class="logo-line" d="M105 150 Q130 130 155 150"/>
            <path class="logo-line" d="M92 155 Q130 180 168 155"/>
            <circle class="logo-fill" cx="130" cy="102" r="23"/>
            <path class="logo-fill" d="M107 102 Q130 80 153 102 L153 126 Q130 143 107 126 Z"/>
            <path class="logo-line" d="M130 80 L130 45"/>
            <path class="logo-line" d="M130 45 L155 55"/>
            <path class="logo-line" d="M70 145 Q45 115 65 88"/>
            <path class="logo-line" d="M190 145 Q215 115 195 88"/>
        </svg>
    </div>

    <div class="blueprint-decoration blueprint-right">BETTER<br>PLACEMENTS<br>BRIGHTER<br>FUTURES</div>
</header>
'''

marker = '<section class="login-card"'
if marker in html and 'class="college-header"' not in html:
    html = html.replace(marker, header + '\n        ' + marker, 1)

# Make the main layout a single centered page.
html = html.replace(
    '<main class="auth-layout">',
    '<main class="auth-layout blueprint-page">'
)

index.write_text(html, encoding="utf-8")

# Add design overrides without destroying existing CSS.
design = r'''

/* =========================================================
   COLLEGE PLACEMENT LOGIN - LIGHT BLUEPRINT DESIGN
   Existing functionality and element IDs are preserved.
   ========================================================= */

html,
body {
    min-height: 100%;
}

body.auth-page {
    margin: 0;
    min-height: 100vh;
    background:
        linear-gradient(rgba(91, 164, 235, 0.10) 1px, transparent 1px),
        linear-gradient(90deg, rgba(91, 164, 235, 0.10) 1px, transparent 1px),
        linear-gradient(135deg, #fafdff 0%, #edf7ff 50%, #f8fcff 100%);
    background-size: 32px 32px, 32px 32px, 100% 100%;
    color: #123b70;
    overflow-x: hidden;
}

/* Blueprint architectural lines */
body.auth-page::before {
    content: "";
    position: fixed;
    inset: 18px;
    border: 1px solid rgba(44, 139, 229, 0.22);
    pointer-events: none;
    z-index: 0;
}

body.auth-page::after {
    content: "";
    position: fixed;
    width: 560px;
    height: 560px;
    left: -180px;
    bottom: -220px;
    border: 2px solid rgba(71, 156, 232, 0.12);
    border-radius: 50%;
    box-shadow:
        0 0 0 35px rgba(71, 156, 232, 0.05),
        0 0 0 70px rgba(71, 156, 232, 0.035);
    pointer-events: none;
    z-index: 0;
}

.blueprint-page {
    position: relative;
    z-index: 1;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    width: 100%;
    max-width: none !important;
    min-height: 100vh;
    padding: 28px 24px 50px !important;
    box-sizing: border-box;
}

/* College title */
.college-header {
    position: relative;
    width: 100%;
    text-align: center;
    margin-bottom: 12px;
}

.college-header h1 {
    margin: 0;
    color: #123f78;
    font-size: clamp(24px, 3vw, 42px);
    font-weight: 800;
    letter-spacing: 1px;
    line-height: 1.15;
}

/* Graduation logo */
.graduation-logo {
    width: 150px;
    height: 125px;
    margin: 8px auto 4px;
}

.graduation-logo svg {
    width: 100%;
    height: 100%;
}

.graduation-logo .logo-line {
    fill: none;
    stroke: #1976d2;
    stroke-width: 5;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.graduation-logo .logo-fill {
    fill: #1976d2;
}

/* Blueprint decorative text */
.blueprint-decoration {
    position: absolute;
    color: rgba(30, 126, 214, 0.42);
    font-size: 14px;
    line-height: 1.45;
    letter-spacing: 2px;
    text-align: left;
    font-weight: 600;
}

.blueprint-left {
    left: 5%;
    top: 50px;
}

.blueprint-right {
    right: 5%;
    top: 65px;
    text-align: right;
}

/* Login card */
.login-card {
    position: relative;
    z-index: 2;
    width: min(700px, 94vw);
    max-width: 700px !important;
    margin: 0 auto !important;
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid rgba(61, 145, 218, 0.22);
    border-radius: 18px;
    box-shadow:
        0 20px 60px rgba(31, 100, 160, 0.13),
        0 4px 15px rgba(31, 100, 160, 0.08);
    padding: 30px !important;
    box-sizing: border-box;
}

/* Role tabs */
.role-picker {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr);
    overflow: hidden;
    border: 1px solid #c8dff5;
    border-radius: 12px;
    background: #fff;
}

.role-tab {
    min-height: 54px;
    border: 0 !important;
    border-right: 1px solid #c8dff5 !important;
    background: #fff !important;
    color: #173d6d !important;
    font-weight: 700;
    cursor: pointer;
    transition: 0.2s ease;
}

.role-tab:last-child {
    border-right: 0 !important;
}

.role-tab:hover {
    background: #edf7ff !important;
}

.role-tab.is-selected {
    background: linear-gradient(135deg, #1479e9, #3198f5) !important;
    color: #fff !important;
}

/* Selected role banner */
.selected-role {
    background: #eaf5ff !important;
    border: 1px solid #d4eaff;
    color: #1266b5 !important;
    border-radius: 9px;
    padding: 12px 14px;
}

/* Inputs */
.login-card input,
.login-card textarea {
    border: 1px solid #c9def2 !important;
    background: #fbfdff !important;
}

.login-card input:focus,
.login-card textarea:focus {
    border-color: #2689e8 !important;
    box-shadow: 0 0 0 3px rgba(38, 137, 232, 0.12) !important;
    outline: none;
}

/* Sign in */
.submit-button {
    background: linear-gradient(135deg, #0878ed, #2498f5) !important;
    border: none !important;
    border-radius: 10px !important;
    min-height: 52px;
    font-weight: 700;
}

/* Create account */
#show-registration {
    display: block;
    width: 100%;
    margin-top: 18px;
    padding: 14px 20px;
    border: 1.5px solid #1885ed;
    border-radius: 10px;
    background: #fff;
    color: #0878ed;
    font-weight: 700;
    text-align: center;
    cursor: pointer;
    transition: 0.2s ease;
}

#show-registration:hover {
    background: #eef8ff;
}

/* Forgot password */
#forgot-password {
    color: #0878ed;
    font-weight: 600;
}

/* Registration panel */
#registration-panel {
    margin-top: 24px;
    border-top: 1px solid #d9e9f7;
    padding-top: 24px;
}

/* Responsive */
@media (max-width: 900px) {
    .blueprint-left,
    .blueprint-right {
        display: none;
    }

    .college-header h1 {
        font-size: 25px;
    }

    .graduation-logo {
        width: 125px;
        height: 105px;
    }
}

@media (max-width: 600px) {
    .blueprint-page {
        padding: 18px 12px 30px !important;
    }

    .college-header h1 {
        font-size: 21px;
        letter-spacing: 0.5px;
    }

    .login-card {
        width: 100%;
        padding: 20px !important;
        border-radius: 14px;
    }

    .role-tab {
        font-size: 13px;
    }
}
'''

with css.open("a", encoding="utf-8") as f:
    f.write(design)

print("==============================================")
print(" LOGIN PAGE REDESIGN COMPLETED")
print("==============================================")
print(f"Updated: {index}")
print(f"Updated: {css}")
print(f"Backup:  {index_backup}")
print(f"Backup:  {css_backup}")
print("")
print("Now refresh the browser with Ctrl + Shift + R")
print("Open: http://localhost:5500/index.html")

