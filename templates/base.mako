<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <link rel="icon" type="image/svg+xml" href="${base_path}/static/img/favicon.svg">
    <link rel="apple-touch-icon" href="${base_path}/static/img/apple-touch-icon.png">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <link href="${base_path}/static/css/style.css" rel="stylesheet">
</head>
<body>
    <script>window.APP_BASE_PATH = "${base_path}";</script>
<%include file="nav.mako"/>
${self.body()}
    <script src="${base_path}/static/js/main.js"></script>
</body>
</html>
