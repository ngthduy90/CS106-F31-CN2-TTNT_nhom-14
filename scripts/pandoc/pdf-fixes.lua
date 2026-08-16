-- table-widths.lua
-- Pandoc pipe tables carry no column widths, so the LaTeX writer splits the text
-- block evenly. That squeezes prose columns next to short ones ("Tuan", "Runbook").
-- This filter sizes each column from the longest cell it holds, dampened with an
-- exponent so a single long cell cannot swallow the table, then clamps and
-- renormalises so the widths still sum to 1.

local EXPONENT = 0.7 -- 1.0 = raw proportional, 0.0 = equal columns
local MIN_W = 0.07   -- no column narrower than 7% of the text block
local MAX_W = 0.45   -- no column wider than 45%

local function cell_length(cell)
  local s = pandoc.utils.stringify(cell.contents)
  return utf8.len(s) or #s
end

local function scan(rows, longest, ncols)
  for _, row in ipairs(rows) do
    local col = 1
    for _, cell in ipairs(row.cells) do
      local span = cell.col_span or 1
      if span == 1 and col <= ncols then
        local n = cell_length(cell)
        if n > longest[col] then longest[col] = n end
      end
      col = col + span
    end
  end
end

function Table(tbl)
  local ncols = #tbl.colspecs
  if ncols < 2 then return nil end

  local longest = {}
  for i = 1, ncols do longest[i] = 1 end

  scan(tbl.head.rows, longest, ncols)
  for _, body in ipairs(tbl.bodies) do scan(body.body, longest, ncols) end
  scan(tbl.foot.rows, longest, ncols)

  local weights, total = {}, 0
  for i = 1, ncols do
    weights[i] = longest[i] ^ EXPONENT
    total = total + weights[i]
  end
  if total == 0 then return nil end

  -- normalise, clamp, then renormalise so the clamping does not overflow the page
  local clamped, sum = {}, 0
  for i = 1, ncols do
    local w = weights[i] / total
    if w < MIN_W then w = MIN_W end
    if w > MAX_W then w = MAX_W end
    clamped[i] = w
    sum = sum + w
  end

  local colspecs = {}
  for i = 1, ncols do
    colspecs[i] = { tbl.colspecs[i][1], clamped[i] / sum }
  end
  tbl.colspecs = colspecs
  return tbl
end

-- Long inline code (URLs, file paths) cannot break in LaTeX and runs past the right
-- margin. Split it into several Code inlines at separator characters, joined with
-- \allowbreak, so the line can wrap. Pandoc still escapes each piece itself.
local MIN_LEN = 24
local SEP = '[/%._%-%?=&:,]'

function Code(el)
  if FORMAT ~= 'latex' then return nil end
  local s = el.text
  if (utf8.len(s) or #s) < MIN_LEN then return nil end

  local out, buf = pandoc.List(), ''
  for ch in s:gmatch(utf8.charpattern) do
    buf = buf .. ch
    if ch:match(SEP) then
      out:insert(pandoc.Code(buf))
      out:insert(pandoc.RawInline('latex', '\\allowbreak{}'))
      buf = ''
    end
  end
  if buf ~= '' then out:insert(pandoc.Code(buf)) end
  if #out <= 1 then return nil end
  return out
end
