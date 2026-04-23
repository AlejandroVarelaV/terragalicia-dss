const http = require('http');

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>TerraGalicia Frontend Placeholder</title>
  </head>
  <body style="font-family: sans-serif; margin: 2rem;">
    <h1>TerraGalicia DSS</h1>
    <p>Frontend placeholder container is running.</p>
  </body>
</html>`;

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
});

server.listen(3000, '0.0.0.0', () => {
  console.log('Frontend placeholder listening on port 3000');
});
