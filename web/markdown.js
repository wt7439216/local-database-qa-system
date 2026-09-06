// 极简安全 markdown 渲染：输入必须是 escapeHtml() 之后的文本。
// 只支持回答实际会用到的结构：# 标题、- 列表、1. 列表、**加粗**、`代码`、```代码块。

function renderMarkdown(escaped) {
  const lines = String(escaped).split(/\r?\n/);
  const out = [];
  let list = null;
  let inCode = false;
  const codeLines = [];

  const inline = (text) => text
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");

  const closeList = () => {
    if (list) {
      out.push(`</${list}>`);
      list = null;
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (inCode) {
      if (/^```/.test(line.trim())) {
        inCode = false;
        out.push(`<pre><code>${codeLines.join("\n")}</code></pre>`);
        codeLines.length = 0;
      } else {
        codeLines.push(line);
      }
      continue;
    }
    if (/^```/.test(line.trim())) {
      closeList();
      inCode = true;
      continue;
    }
    if (!line.trim()) {
      closeList();
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      closeList();
      const level = Math.min(heading[1].length + 2, 6);
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      continue;
    }
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    if (bullet) {
      if (list !== "ul") {
        closeList();
        out.push("<ul>");
        list = "ul";
      }
      out.push(`<li>${inline(bullet[1])}</li>`);
      continue;
    }
    const numbered = line.match(/^\d+[.、)）]\s+(.*)$/);
    if (numbered) {
      if (list !== "ol") {
        closeList();
        out.push("<ol>");
        list = "ol";
      }
      out.push(`<li>${inline(numbered[1])}</li>`);
      continue;
    }
    closeList();
    out.push(`<p>${inline(line)}</p>`);
  }
  if (inCode && codeLines.length) {
    out.push(`<pre><code>${codeLines.join("\n")}</code></pre>`);
  }
  closeList();
  return out.join("");
}
