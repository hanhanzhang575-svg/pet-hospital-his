import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(__dirname, "..");
const distRoot = join(frontendRoot, "dist");
const aliasDirName = "20231111085-\u7ba1\u4fe12301\u5f20\u9ed8\u6db5";
const projectEntryHash = "#/20231111085-%E7%AE%A1%E4%BF%A12301%E5%BC%A0%E9%BB%98%E6%B6%B5";

const aliasDir = join(distRoot, aliasDirName);
const sourceHtml = join(distRoot, "index.html");
const aliasHtml = join(aliasDir, "index.html");

let html = await readFile(sourceHtml, "utf8");
html = html.replaceAll('"./assets/', '"../assets/');
html = html.replaceAll('"./login-pet-bg.jpg', '"../login-pet-bg.jpg');
html = html.replace(
  "</head>",
  `    <script>if(!location.hash){location.replace(location.pathname+location.search+"${projectEntryHash}")}</script>\n  </head>`
);

await mkdir(aliasDir, { recursive: true });
await writeFile(aliasHtml, html, "utf8");

console.log(`Created GitHub Pages alias: ${aliasDirName}/`);
