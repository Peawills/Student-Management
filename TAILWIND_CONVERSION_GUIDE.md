# Tailwind CSS Conversion Guide

This document outlines the conversion from Bootstrap to Tailwind CSS for all templates in the Student Management System.

## Completed Conversions

### Base Templates
- ✅ `records/templates/records/base.html` - Main base template with navigation
- ✅ `portal/templates/portal/base.html` - Portal base template (if exists)

### Account Templates
- ✅ `accounts/templates/accounts/login.html` - Login page

### Records Templates
- ✅ `records/templates/records/homepage.html` - Homepage (already had Tailwind)
- ✅ `records/templates/records/student_list.html` - Student list (already had Tailwind)
- ✅ `records/templates/records/student_detail.html` - Student detail (already had Tailwind)
- ✅ `records/templates/records/student_form.html` - Student form (already had Tailwind)

### Academics Templates
- ✅ `academics/templates/academics/dashboard.html` - Academics dashboard
- ✅ `academics/templates/academics/assignment_list.html` - Assignment list
- ✅ `academics/templates/academics/subject_list.html` - Subject list
- ✅ `academics/templates/academics/subject_form.html` - Subject form

## Conversion Patterns

### Common Bootstrap to Tailwind Mappings

#### Containers
```html
<!-- Bootstrap -->
<div class="container-fluid p-4">
<div class="container py-4">

<!-- Tailwind -->
<div class="container mx-auto px-4 py-6">
```

#### Buttons
```html
<!-- Bootstrap -->
<button class="btn btn-primary">
<a class="btn btn-outline-primary">

<!-- Tailwind -->
<button class="px-5 py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors">
<a class="px-5 py-2.5 border-2 border-primary-500 text-primary-600 font-semibold rounded-lg hover:bg-primary-50 transition-colors">
```

#### Cards
```html
<!-- Bootstrap -->
<div class="card shadow-sm">
  <div class="card-body">

<!-- Tailwind -->
<div class="bg-white rounded-2xl shadow-lg p-6">
```

#### Tables
```html
<!-- Bootstrap -->
<table class="table table-hover">
  <thead class="table-light">

<!-- Tailwind -->
<table class="w-full">
  <thead class="bg-gray-50">
    <tr class="hover:bg-gray-50 transition-colors">
```

#### Forms
```html
<!-- Bootstrap -->
<input class="form-control">
<label class="form-label">

<!-- Tailwind -->
<input class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500">
<label class="block text-sm font-semibold text-gray-700 mb-2">
```

#### Badges
```html
<!-- Bootstrap -->
<span class="badge bg-primary">

<!-- Tailwind -->
<span class="px-2 py-1 text-xs font-semibold rounded-full bg-primary-100 text-primary-700">
```

#### Alerts
```html
<!-- Bootstrap -->
<div class="alert alert-success">

<!-- Tailwind -->
<div class="p-4 rounded-xl bg-green-50 text-green-800 border-l-4 border-green-500">
```

#### Grid System
```html
<!-- Bootstrap -->
<div class="row">
  <div class="col-md-6 col-lg-4">

<!-- Tailwind -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
```

#### Flexbox
```html
<!-- Bootstrap -->
<div class="d-flex justify-content-between align-items-center">

<!-- Tailwind -->
<div class="flex justify-between items-center">
```

#### Spacing
```html
<!-- Bootstrap -->
<div class="mb-4 mt-3 p-4">

<!-- Tailwind -->
<div class="mb-6 mt-4 p-6">
```

## Remaining Templates to Convert

### Records App (12 templates)
- [ ] `records/templates/records/admin_dashboard.html`
- [ ] `records/templates/records/alumni_list.html`
- [ ] `records/templates/records/student_confirm_delete.html`
- [ ] `records/templates/records/upload_document.html`
- [ ] `records/templates/records/student_creation_success.html`
- [ ] `records/templates/records/document_confirm_delete.html`
- [ ] `records/templates/records/general_home.html`

### Academics App (36 templates)
- [ ] All remaining list templates (classroom, session, term, assessment, etc.)
- [ ] All remaining form templates
- [ ] Detail templates
- [ ] Report card templates
- [ ] Analytics templates
- [ ] Attendance templates
- [ ] Timetable templates

### Portal App (23 templates)
- [ ] Dashboard templates
- [ ] Profile templates
- [ ] Message templates
- [ ] Announcement templates
- [ ] Student/Parent portal templates

### Accounts App (5 templates)
- [ ] `accounts/templates/accounts/user_list.html`
- [ ] `accounts/templates/accounts/user_detail.html`
- [ ] `accounts/templates/accounts/user_form.html`
- [ ] `accounts/templates/accounts/user_confirm_delete.html`

### Committee App (6 templates)
- [ ] `committee/templates/committee/offense_list.html`
- [ ] `committee/templates/committee/offense_form.html`
- [ ] `committee/templates/committee/offense_detail.html`
- [ ] `committee/templates/committee/offense_confirm_delete.html`
- [ ] `committee/templates/committee/offense_pdf.html`
- [ ] `committee/templates/committee/analytics_dashboard.html`

## Tailwind Configuration

The base template includes Tailwind CSS via CDN with custom color configuration:

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: {
                    500: '#667eea',
                    600: '#5568d3',
                    // ... more shades
                },
                secondary: {
                    500: '#764ba2',
                    // ... more shades
                }
            }
        }
    }
}
```

## Best Practices

1. **Use Tailwind utility classes** instead of custom CSS where possible
2. **Maintain responsive design** using Tailwind's responsive prefixes (sm:, md:, lg:, xl:)
3. **Keep animations smooth** using Tailwind's transition utilities
4. **Use consistent spacing** following Tailwind's spacing scale
5. **Leverage Tailwind's color system** for consistent theming
6. **Use flexbox and grid** utilities for layouts instead of Bootstrap's grid system

## Testing Checklist

After converting each template:
- [ ] Verify responsive design on mobile, tablet, and desktop
- [ ] Check all buttons and links are clickable
- [ ] Verify forms submit correctly
- [ ] Test dropdown menus and modals
- [ ] Check color contrast for accessibility
- [ ] Verify animations and transitions work smoothly
- [ ] Test with different user roles (admin, teacher, student, parent)

## Notes

- Bootstrap Icons are still used via CDN (no change needed)
- All JavaScript functionality remains the same
- Form validation and Django form rendering should work as before
- The base template handles navigation and common UI elements

