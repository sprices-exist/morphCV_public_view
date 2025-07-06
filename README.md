# 🌐 morphCV_public_view

> A public-facing demo of morphCV with active Stripe subscription flow and landing page preview.

---

### ⚠️ Status Notice
> **This repository is a few commits behind** the main development branch.

---

## 🖼️ Preview Screens

### 🚀 Landing Page
![image](https://github.com/user-attachments/assets/9ee45da9-ce41-46a2-9da9-569d765ff220)

---

### 📄 Active Subscription Status
![image](https://github.com/user-attachments/assets/ecd40d6c-79fa-430d-9c34-2a639cf6f6b2)

---

### 💳 Stripe Checkout Page
![image](https://github.com/user-attachments/assets/1319bf70-9b88-4db6-a8aa-43ca345c7b37)

---

## 🧾 Description

This project demonstrates:
- A clean landing page interface
- Stripe subscription integration
- Active subscription status handling
- A minimal public view version of the morphCV product

---

## 📦 Tech Stack

- React, flask, docker, LaTeX, celery, redist, postgreSQL
- Stripe API, google OAuth API

---

## 📁 Repository Structure

|   README.md
|
+---flask_backend
|   |   celerybeat-schedule
|   |   cv.pdf
|   |   docker-compose.yml
|   |   Dockerfile
|   |   fetch.ps1
|   |   gunicorn.conf.py
|   |   list_of_cvs.txt
|   |   output1.txt
|   |   README.md
|   |   requirements.txt
|   |   run.py
|   |
|   +---app
|   |   |   config.py
|   |   |   models.py
|   |   |   __init__.py
|   |   |
|   |   +---api
|   |   |       auth.py
|   |   |       cvs.py
|   |   |       subscription.py
|   |   |       users.py
|   |   |       __init__.py
|   |   |
|   |   +---main
|   |   |       routes.py
|   |   |       __init__.py
|   |   |
|   |   +---services
|   |   |       auth_service.py
|   |   |       cv_service.py
|   |   |       gemini_service.py
|   |   |       latex_service.py
|   |   |       payment_service.py
|   |   |
|   |   +---tasks
|   |   |       cv_tasks.py
|   |   |
|   |   \---utils
|   |           decorators.py
|   |           validators.py
|   |
|   +---latex_templates
|   |       template_1.tex
|   |       template_2.tex
|   |       template_3.tex
|   |       template_4.tex
|   |
|   \---migrations
|       |   alembic.ini
|       |   env.py
|       |   README
|       |   script.py.mako
|       |
|       \---versions
|               0708ff47c2d5_.py
|               1f303c3e9a88_convert_datetime_columns_to_use_.py
|
\---morphcv
    |   .gitignore
    |   components.json
    |   DEPLOYMENT.md
    |   eslint.config.js
    |   fetch.ps1
    |   index.html
    |   INTEGRATION_CHECKLIST.md
    |   INTEGRATION_TEST.md
    |   output1.txt
    |   package.json
    |   pnpm-lock.yaml
    |   postcss.config.js
    |   README.docx
    |   README.md
    |   README.pdf
    |   tailwind.config.js
    |   tsconfig.app.json
    |   tsconfig.json
    |   tsconfig.node.json
    |   update-env.sh
    |   vite.config.ts
    |
    +---dist
    |   |   index.html
    |   |   use.txt
    |   |
    |   +---assets
    |   |       index-33z_w-PK.css
    |   |       index-BxHgyEfP.js
    |   |
    |   \---images
    |       \---templates
    |               template_1_preview.png
    |               template_2_preview.webp
    |               template_3_preview.jpg
    |               template_4_preview.png
    |
    +---public
    |   |   use.txt
    |   |
    |   \---images
    |       \---templates
    |               template_1_preview.png
    |               template_2_preview.webp
    |               template_3_preview.jpg
    |               template_4_preview.png
    |
    \---src
        |   App.css
        |   App.tsx
        |   index.css
        |   main.tsx
        |   vite-env.d.ts
        |
        +---components
        |   |   ErrorBoundary.tsx
        |   |
        |   +---MainApp
        |   |       StatusTracker.tsx
        |   |       TemplateSelector.tsx
        |   |
        |   +---shared
        |   |       ErrorDisplay.tsx
        |   |       FloatingParticles.tsx
        |   |       LoadingSpinner.tsx
        |   |       Navigation.tsx
        |   |       ProtectedRoute.tsx
        |   |
        |   \---ui
        |           accordion.tsx
        |           alert-dialog.tsx
        |           alert.tsx
        |           aspect-ratio.tsx
        |           avatar.tsx
        |           badge.tsx
        |           breadcrumb.tsx
        |           button.tsx
        |           calendar.tsx
        |           card.tsx
        |           carousel.tsx
        |           chart.tsx
        |           checkbox.tsx
        |           collapsible.tsx
        |           command.tsx
        |           context-menu.tsx
        |           dialog.tsx
        |           drawer.tsx
        |           dropdown-menu.tsx
        |           form.tsx
        |           hover-card.tsx
        |           input-otp.tsx
        |           input.tsx
        |           label.tsx
        |           menubar.tsx
        |           navigation-menu.tsx
        |           pagination.tsx
        |           popover.tsx
        |           progress.tsx
        |           radio-group.tsx
        |           resizable.tsx
        |           scroll-area.tsx
        |           select.tsx
        |           separator.tsx
        |           sheet.tsx
        |           sidebar.tsx
        |           skeleton.tsx
        |           slider.tsx
        |           sonner.tsx
        |           switch.tsx
        |           table.tsx
        |           tabs.tsx
        |           textarea.tsx
        |           toast.tsx
        |           toaster.tsx
        |           toggle-group.tsx
        |           toggle.tsx
        |           tooltip.tsx
        |
        +---contexts
        |       AuthContext.tsx
        |
        +---hooks
        |       use-mobile.tsx
        |       use-toast.ts
        |
        +---lib
        |   |   utils.ts
        |   |
        |   +---api
        |   |       apiClient.ts
        |   |       authService.ts
        |   |       cvService.ts
        |   |       index.ts
        |   |       subscriptionService.ts
        |   |       userService.ts
        |   |
        |   \---utils
        |           environmentSetup.ts
        |
        \---pages
                CVEditPage.tsx
                CVListPage.tsx
                GoogleLoginPage.tsx
                LandingPage.tsx
                MainAppPage.tsx
                SubscriptionPage.tsx
