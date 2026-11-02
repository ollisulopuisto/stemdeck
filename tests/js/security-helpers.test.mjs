import { isWikipediaUrl } from "../helpers/url.mjs";
import assert from "node:assert/strict";
import { escapeHtml, lyricText, tableCell } from "../helpers/text.mjs";
assert.equal(escapeHtml(`<img onerror="x"> & 'text'`), "&lt;img onerror=&quot;x&quot;&gt; &amp; &#39;text&#39;");
assert.equal(escapeHtml("&lt;script&gt;"), "&amp;lt;script&amp;gt;");
assert.equal(lyricText("<00:01.20>Server <00:01.80>one"), "Server one");
assert.equal(lyricText("<scr<script>ipt>ok</scr</script>ipt>"), "ok");
assert.equal(lyricText("A & B <unfinished"), "A  B unfinished");

// A Markdown table cell must never leak its column or row boundary characters.
assert.equal(tableCell("a|b"), "a\\|b", "pipe is escaped so it cannot split the cell");
assert.equal(tableCell("a\nb"), "a b", "newline is collapsed so it cannot start a row");
assert.equal(tableCell("a\r\nb"), "a b", "CRLF is collapsed so it cannot start a row");
assert.equal(tableCell("<img onerror=x>"), "&lt;img onerror=x&gt;", "HTML is still escaped");
for (const host of ["en.wikipedia.org", "zh-min-nan.wikipedia.org"]) assert(isWikipediaUrl(`https://${host}/w/api.php`));
for (const url of ["https://evilwikipedia.org", "https://en.wikipedia.org.evil.test", "https://wikipedia.org", "https://en.wikipedia.org:999", "http://en.wikipedia.org", "https://user@en.wikipedia.org"]) assert(!isWikipediaUrl(url), url);
console.log("security helper cases passed");
