<div align="center">

<img src="banner.svg" width="100%" alt="Super DM VPN Panel">

<a href="https://t.me/+WvKFv0lU_i5lNGE0"><img src="https://readme-typing-svg.demolab.com?font=Inter&weight=800&size=22&duration=2600&pause=700&color=6C7BFF&center=true&vCenter=true&width=620&lines=One-click+Reseller+Panel+on+Railway;PasarGuard+%2B+Xray+in+a+single+service;5+configs+%C2%B7+2+groups+%C2%B7+self-healing;Free+forever+%C2%B7+X4G+%C3%97+DM+VPN" alt="Super DM VPN"></a>

<h1>Super DM VPN Panel</h1>

<p><b>پنل نمایندگی حرفه‌ای، رایگان و متن‌باز بر پایه‌ی PasarGuard</b><br>
یک Fork تا یک سرویس کامل: پنل، هسته‌ی Xray و 5 کانفیگ آماده، همه روی Railway</p>

<a href="https://t.me/+WvKFv0lU_i5lNGE0"><img src="https://img.shields.io/badge/Telegram-Super%20DM%20VPN-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"></a>
<img src="https://img.shields.io/badge/Version-6.1.3-5b6cff?style=for-the-badge" alt="Version">
<img src="https://img.shields.io/badge/Price-Free-16a34a?style=for-the-badge" alt="Free">
<br>
<img src="https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white" alt="Railway">
<img src="https://img.shields.io/badge/Panel-PasarGuard-1e3a8a?style=for-the-badge" alt="PasarGuard">
<img src="https://img.shields.io/badge/Core-Xray-7c4dff?style=for-the-badge" alt="Xray">
<img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">

<br><br>

<a href="../../fork"><img src="https://img.shields.io/badge/Fork%20%D9%88%20%D9%86%D8%B5%D8%A8%20%D8%B1%D8%A7%DB%8C%DA%AF%D8%A7%D9%86-5b6cff?style=for-the-badge&logo=github&logoColor=white" alt="Fork"></a>
<a href="https://railway.com/new"><img src="https://img.shields.io/badge/Deploy%20on%20Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white" alt="Deploy on Railway"></a>

<br><br>

<a href="#preview"><b>پیش‌نمایش</b></a> &nbsp;·&nbsp;
<a href="#install"><b>نصب</b></a> &nbsp;·&nbsp;
<a href="#guides"><b>آموزش‌ها</b></a> &nbsp;·&nbsp;
<a href="#configs"><b>کانفیگ‌ها</b></a> &nbsp;·&nbsp;
<a href="#reseller"><b>نمایندگی</b></a> &nbsp;·&nbsp;
<a href="#fix"><b>عیب‌یابی</b></a> &nbsp;·&nbsp;
<a href="https://t.me/+WvKFv0lU_i5lNGE0"><b>کانال</b></a>

</div>

<br>

> [!NOTE]
> **Super DM VPN** کاملاً رایگانه. ریپو رو Fork کن، روی Railway بساز و در کمتر از 5 دقیقه پنل نمایندگی خودت رو تحویل بگیر. بدون VPS، بدون ترمینال، بدون تنظیم دستی.

<br>

> [!IMPORTANT]
> **تازه‌های نسخه‌ی 6.1.3:** صفحه‌ی اشتراک جدید DM VPN PASS دو زبانه · نگهبان ساب لینک 3 ثانیه‌ای · پینگ پایدارتر و مصرف رم کمتر · ربات پشتیبان خودکار که هر خرابی رو همونجا درست می‌کنه · تغییر رمز از داخل تنظیمات · بازیابی ورود با کلید مالک از صفحه‌ی ورود · قفل گروه‌ها و هاست‌ها در برابر حذف · کانفیگ‌های سریع‌تر · صفحه‌ی اشتراک مقاوم‌تر

<br>

<div align="center">

| <img src="ic-features.svg" width="34"><br>**1 سرویس** | <img src="ic-configs.svg" width="34"><br>**5 کانفیگ** | <img src="ic-reseller.svg" width="34"><br>**2 گروه** | <img src="ic-sub.svg" width="34"><br>**10 قالب فروش** | <img src="ic-apps.svg" width="34"><br>**6 اپ** | <img src="ic-heal.svg" width="34"><br>**خودترمیم** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| پنل + Xray + nginx | 3 پروتکل، 2 انتقال | پرو و DM VPN | آماده‌ی فروش | اتصال با یک لمس | 24 ساعته |

</div>

<br>

<a id="preview"></a>
## <img src="ic-sub.svg" width="30" align="center"> &nbsp;پیش‌نمایش

<div align="center">

<img src="preview.png" width="100%" alt="Super DM VPN subscription page: DM VPN PASS">

<sub>صفحه‌ی اشتراکی که مشتری‌هات می‌بینن: کارت هولوگرامی DM VPN PASS، پینگ زنده، QR داخلی و اتصال با یک لمس، به فارسی و انگلیسی</sub>

</div>

<br>

### <img src="ic-install.svg" width="24" align="center"> &nbsp;شروع سریع در 5 قدم

```mermaid
flowchart LR
    A["Fork<br/>GitHub"] --> B["Deploy<br/>Railway"]
    B --> C["Volume<br/>/var/lib/pasarguard"]
    C --> D["Domain<br/>port 8080"]
    D --> E["Region<br/>EU West"]
    E --> F(("Ready"))
    style F fill:#5b6cff,stroke:#a855f7,color:#fff
