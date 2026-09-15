// Dựng slide thuyết trình PowerPoint cho buổi bảo vệ đồ án, theo khung reports/slides/slides.md.
//
//   npm install pptxgenjs react react-dom react-icons sharp   (ở một thư mục tạm bất kỳ)
//   NODE_PATH=<thư mục đó>/node_modules node reports/slides/deck/build-deck.js
//
// Khác bản pandoc (scripts/build-slides.sh): bản này có bố cục, hình vẽ lại và ghi chú
// người nói. Mọi con số chép từ reports/tables/*.md; bảng đổi thì sửa số ở đây theo.

const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");

const ROOT = path.resolve(__dirname, "../../..");
const OUT = path.join(ROOT, "reports/slides/slide-thuyet-trinh.pptx");

const C = {
  ink: "13303A", ink2: "1F4A57", inkSoft: "1C4250",
  terra: "C8553A", terraSoft: "FBEAE3", terraOnDark: "F2A283",
  mist: "EAF2F3", line: "D3DFE2", muted: "5B6D74", text: "1B2A30",
  green: "2F8F5B", white: "FFFFFF", onDarkMuted: "B4CAD0",
};
const FONT = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,333 × 7,5 inch
pres.author = "Nhóm 14 · CS106.F31.CN2";
pres.title = "Dự báo giá nhà TP.HCM từ dữ liệu rao vặt";

// ---------- tiện ích vẽ ----------

async function icon(name, color) {
  const Comp = fa[name];
  if (!Comp) throw new Error(`react-icons/fa6 không có ${name}`);
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { size: 256 }))
    .replace(/currentColor/g, "#" + color);
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function text(slide, value, o) {
  slide.addText(value, { fontFace: FONT, color: C.text, margin: 0, valign: "top", isTextBox: true, ...o });
}

function box(slide, x, y, w, h, fill, o = {}) {
  slide.addShape(o.square ? pres.shapes.RECTANGLE : pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: fill },
    line: { color: o.border || fill, width: o.border ? 1 : 0 },
    ...(o.square ? {} : { rectRadius: o.radius ?? 0.1 }),
    ...(o.shadow ? { shadow: { type: "outer", color: "000000", opacity: 0.1, blur: 10, offset: 2, angle: 90 } } : {}),
  });
}

function line(slide, x1, y1, x2, y2, o = {}) {
  slide.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1,
    line: { color: o.color || C.muted, width: o.width || 1.25, dashType: o.dash || "solid", endArrowType: o.arrow ? "triangle" : undefined },
  });
}

async function iconCircle(slide, name, x, y, d, fill, color) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 } });
  const s = d * 0.5;
  slide.addImage({ data: await icon(name, color), x: x + (d - s) / 2, y: y + (d - s) / 2, w: s, h: s });
}

function header(slide, n, kicker, title) {
  slide.background = { color: C.white };
  box(slide, 0.6, 0.5, 0.52, 0.32, C.terra, { radius: 0.06 });
  text(slide, String(n).padStart(2, "0"), { x: 0.6, y: 0.5, w: 0.52, h: 0.32, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle" });
  text(slide, kicker.toUpperCase(), { x: 1.27, y: 0.5, w: 9, h: 0.32, fontSize: 12, bold: true, color: C.terra, charSpacing: 1.5, valign: "middle" });
  text(slide, title, { x: 0.6, y: 0.9, w: 12.1, h: 0.75, fontSize: 32, bold: true, color: C.ink, valign: "middle" });
  text(slide, "Dự báo giá nhà TP.HCM từ dữ liệu rao vặt · Nhóm 14", { x: 0.6, y: 7.02, w: 8, h: 0.28, fontSize: 10, color: C.muted, valign: "middle" });
  text(slide, "CS106.F31.CN2", { x: 9.7, y: 7.02, w: 3.0, h: 0.28, fontSize: 10, color: C.muted, align: "right", valign: "middle" });
}

const b = (t, extra = {}) => ({ text: t, options: { bold: true, ...extra } });
const r = (t, extra = {}) => ({ text: t, options: { ...extra } });

// ---------- các slide ----------

async function main() {
  // 1 · Bìa
  {
    const s = pres.addSlide();
    s.background = { color: C.ink };
    text(s, "CS106.F31.CN2 · ĐỒ ÁN ĐỀ TÀI 5 · NHÓM 14", { x: 0.7, y: 0.85, w: 7, h: 0.4, fontSize: 13, bold: true, color: C.terraOnDark, charSpacing: 1.5 });
    text(s, "Dự báo giá nhà TP.HCM từ dữ liệu rao vặt", { x: 0.7, y: 1.35, w: 7.0, h: 2.3, fontSize: 46, bold: true, color: C.white });
    text(s, "Thu thập tin rao, trích đặc trưng từ mô tả tự do, chuẩn hoá địa chỉ qua đợt sáp nhập 2025, rồi so sánh 12 mô hình hồi quy trên cùng một bộ fold.",
      { x: 0.7, y: 3.75, w: 6.8, h: 1.1, fontSize: 16, color: C.onDarkMuted });
    const stats = [["34.607", "dòng dữ liệu\nsau làm sạch"], ["12", "mô hình\nchia 4 tầng"], ["6,32–6,66", "điểm % MdAPE thấp\nhơn baseline môi giới"]];
    stats.forEach(([num, label], i) => {
      const x = 0.7 + i * 2.35;
      text(s, num, { x, y: 5.15, w: 2.2, h: 0.55, fontSize: 28, bold: true, color: C.white });
      text(s, label, { x, y: 5.72, w: 2.2, h: 0.6, fontSize: 12, color: C.onDarkMuted });
    });
    text(s, "2026", { x: 0.7, y: 6.75, w: 2, h: 0.3, fontSize: 12, color: C.onDarkMuted });

    box(s, 8.2, 0.8, 4.5, 5.95, C.inkSoft, { radius: 0.12 });
    text(s, "Thành viên nhóm", { x: 8.5, y: 1.0, w: 3.9, h: 0.45, fontSize: 17, bold: true, color: C.white });
    const members = [
      ["Lê Phú Hiếu", "26410038", "LT.K2026.1.TTNT"],
      ["Nguyễn Thanh Duy", "26410030", "LT.K2026.1.TTNT"],
      ["Nguyễn Thanh Phong", "26410090", "LT.K2026.1.TTNT"],
      ["Nguyễn Thị Mai Thi", "26410117", "LT.K2026.1.TTNT"],
      ["Hồ Viết Trịnh", "26410140", "LT.K2026.1.TTNT"],
      ["Nguyễn Ngọc Bích", "25730012", "CN1.K2025.1.TTNT"],
      ["Nguyễn Anh Tài", "25730063", "CN1.K2025.1.TTNT"],
    ];
    members.forEach(([name, mssv, lop], i) => {
      const y = 1.6 + i * 0.72;
      text(s, name, { x: 8.5, y, w: 3.9, h: 0.34, fontSize: 15, bold: true, color: C.white });
      text(s, `${mssv} · ${lop}`, { x: 8.5, y: y + 0.33, w: 3.9, h: 0.28, fontSize: 11.5, color: C.onDarkMuted });
    });
    s.addNotes(
      "Kính chào thầy cô và các bạn. Nhóm 14 trình bày đồ án đề tài 5: dự báo giá nhà TP.HCM từ dữ liệu rao vặt. " +
      "Nhóm có bảy thành viên như trên slide.\n\n" +
      "Bài trình bày đi qua bốn phần: dữ liệu và cách làm sạch, trích đặc trưng từ văn bản, kết quả các thí nghiệm, rồi demo và hạn chế."
    );
  }

  // 2 · Bài toán
  {
    const s = pres.addSlide();
    header(s, 2, "Đặt vấn đề", "Bài toán");
    text(s, [r("Ước lượng "), b("tổng giá rao", { color: C.terra }), r(" của một bất động sản tại TP.HCM từ hai loại đầu vào:")],
      { x: 0.6, y: 1.95, w: 6.1, h: 0.95, fontSize: 20 });
    const inputs = [
      ["FaTableList", "Thuộc tính có cấu trúc", "diện tích, phòng ngủ, số tầng, vị trí, pháp lý"],
      ["FaQuoteLeft", "Mô tả tự do của tin rao", "phần người bán tự viết, form của sàn không ép khuôn"],
    ];
    for (const [i, [ic, head, detail]] of inputs.entries()) {
      const y = 3.1 + i * 1.25;
      await iconCircle(s, ic, 0.6, y, 0.8, C.mist, C.ink2);
      text(s, head, { x: 1.6, y: y + 0.02, w: 5.1, h: 0.4, fontSize: 18, bold: true, color: C.ink });
      text(s, detail, { x: 1.6, y: y + 0.42, w: 5.1, h: 0.4, fontSize: 15, color: C.muted });
    }

    box(s, 7.1, 1.95, 5.6, 3.55, C.white, { border: C.line, shadow: true });
    text(s, "Mô tả chứa thứ form không có", { x: 7.4, y: 2.12, w: 5.0, h: 0.45, fontSize: 17, bold: true, color: C.ink });
    const chips = [
      ["“hẻm xe hơi”", "ô tô vào tận cửa"],
      ["“nở hậu”", "phía sau rộng hơn mặt tiền"],
      ["“ngộp bank”", "chủ kẹt nợ ngân hàng, cần bán gấp"],
      ["“sổ hồng riêng”", "pháp lý tách riêng, rõ ràng"],
    ];
    chips.forEach(([phrase, gloss], i) => {
      const x = 7.4 + (i % 2) * 2.6, y = 2.7 + Math.floor(i / 2) * 1.35;
      box(s, x, y, 2.45, 1.2, C.terraSoft);
      text(s, phrase, { x: x + 0.18, y: y + 0.18, w: 2.1, h: 0.42, fontSize: 18, bold: true, color: C.terra });
      text(s, gloss, { x: x + 0.18, y: y + 0.6, w: 2.15, h: 0.5, fontSize: 12, color: C.text });
    });

    box(s, 0.6, 5.85, 12.1, 0.95, C.ink);
    text(s, [b("Câu hỏi trung tâm: ", { color: C.terraOnDark }), b("phần văn bản đó đáng bao nhiêu?", { color: C.white })],
      { x: 0.95, y: 5.85, w: 8.6, h: 0.95, fontSize: 24, valign: "middle" });
    text(s, "Trả lời ở slide 13 (ablation)", { x: 9.4, y: 5.85, w: 3.05, h: 0.95, fontSize: 13, color: C.onDarkMuted, align: "right", valign: "middle" });
    s.addNotes(
      "Bài toán là ước lượng tổng giá rao của một bất động sản. Đầu vào có hai loại.\n\n" +
      "Loại thứ nhất là các trường người bán điền vào form: diện tích, phòng ngủ, số tầng, vị trí, pháp lý.\n\n" +
      "Loại thứ hai là phần mô tả tự viết. Phần này chứa những thứ form không hỏi: hẻm xe hơi, nở hậu, ngộp bank, sổ hồng riêng. " +
      "Ai từng đi mua nhà đều biết mấy chữ đó kéo giá lên hoặc xuống.\n\n" +
      "Câu hỏi nhóm đặt ra: phần văn bản đó đáng bao nhiêu, đo được bằng con số. Câu trả lời nằm ở slide ablation."
    );
  }

  // 3 · Ba nguồn dữ liệu
  {
    const s = pres.addSlide();
    header(s, 3, "Dữ liệu", "Ba nguồn dữ liệu");
    const sources = [
      { ic: "FaCode", role: "Hiện tại", roleFill: C.terra, name: "Chợ Tốt", method: [r("API JSON công khai, quét theo quận")], clean: "2.326", raw: "từ 2.400 tin thô" },
      { ic: "FaGlobe", role: "Hiện tại", roleFill: C.terra, name: "mogi.vn", method: [r("Parse HTML: trang danh sách → trang chi tiết")], clean: "334", raw: "từ 360 tin thô" },
      { ic: "FaDatabase", role: "Lịch sử", roleFill: C.ink2, name: "Hugging Face", method: [r("Tải parquet bộ", { breakLine: true }), r("tinixai/vietnam-real-estates", { fontFace: "Courier New", fontSize: 12.5 })], clean: "31.947", raw: "từ 40.000 tin thô" },
    ];
    for (const [i, src] of sources.entries()) {
      const x = 0.6 + i * 4.1, y = 1.95, w = 3.9;
      box(s, x, y, w, 3.25, C.mist);
      await iconCircle(s, src.ic, x + 0.3, y + 0.3, 0.72, C.white, C.ink2);
      box(s, x + w - 1.45, y + 0.48, 1.15, 0.36, src.roleFill, { radius: 0.18 });
      text(s, src.role, { x: x + w - 1.45, y: y + 0.48, w: 1.15, h: 0.36, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle" });
      text(s, src.name, { x: x + 0.3, y: y + 1.15, w: w - 0.6, h: 0.45, fontSize: 21, bold: true, color: C.ink });
      text(s, src.method, { x: x + 0.3, y: y + 1.6, w: w - 0.6, h: 0.7, fontSize: 14.5 });
      text(s, [b(src.clean, { fontSize: 28, color: C.terra }), r("  tin sau làm sạch", { fontSize: 13, color: C.text })],
        { x: x + 0.3, y: y + 2.28, w: w - 0.6, h: 0.5, valign: "bottom" });
      text(s, src.raw, { x: x + 0.3, y: y + 2.8, w: w - 0.6, h: 0.3, fontSize: 12, color: C.muted });
    }
    text(s, "Ranh giới tự đặt khi thu thập", { x: 0.6, y: 5.45, w: 6, h: 0.4, fontSize: 16, bold: true, color: C.ink });
    const rules = [
      ["FaRobot", "Tôn trọng robots.txt"],
      ["FaShieldHalved", "Không vượt anti-bot chủ động"],
      ["FaHourglassHalf", "1 request mỗi 1,5 giây"],
      ["FaUserSecret", "Không thu thập thông tin người bán"],
    ];
    for (const [i, [ic, label]] of rules.entries()) {
      const x = 0.6 + i * 3.07;
      await iconCircle(s, ic, x, 5.98, 0.62, C.terraSoft, C.terra);
      text(s, label, { x: x + 0.75, y: 5.98, w: 2.2, h: 0.62, fontSize: 14, valign: "middle" });
    }
    s.addNotes(
      "Dữ liệu đến từ ba nguồn.\n\n" +
      "Hai nguồn hiện tại: Chợ Tốt, lấy qua API JSON công khai, quét theo từng quận; và mogi.vn, parse HTML từ trang danh sách vào trang chi tiết.\n\n" +
      "Nguồn lịch sử là bộ vietnam-real-estates trên Hugging Face, tải dạng parquet.\n\n" +
      "Con số lớn trên mỗi thẻ là số tin còn lại sau làm sạch.\n\n" +
      "Khi thu thập, nhóm tự đặt bốn ranh giới: tôn trọng robots.txt, không vượt anti-bot, một request mỗi 1,5 giây, và không thu thập thông tin người bán.\n\n" +
      "Nếu được hỏi vì sao kho thô không có trong repo: tin rao có thể còn dấu vết người bán, và bộ Hugging Face có license CC BY-NC 4.0 cấm tái phân phối. Chạy make crawl để dựng lại."
    );
  }

  // 4 · Xoá số điện thoại
  {
    const s = pres.addSlide();
    header(s, 4, "Dữ liệu · Quyền riêng tư", "Xoá số điện thoại ngay lúc ghi file");
    text(s, "Người rao né bộ lọc của sàn bằng đủ kiểu:", { x: 0.6, y: 1.95, w: 5.2, h: 0.45, fontSize: 16 });
    const tricks = [
      ["FaHashtag", "Chữ số Unicode"],
      ["FaFaceSmile", "Emoji thay chữ số"],
      ["FaFont", "Chữ cái thay số"],
      ["FaSpellCheck", "Số viết bằng chữ"],
      ["FaEyeSlash", "Ký tự vô hình chèn giữa"],
    ];
    for (const [i, [ic, label]] of tricks.entries()) {
      const y = 2.55 + i * 0.82;
      box(s, 0.6, y, 5.0, 0.66, C.mist);
      s.addImage({ data: await icon(ic, C.ink2), x: 0.85, y: y + 0.16, w: 0.34, h: 0.34 });
      text(s, label, { x: 1.4, y, w: 4.0, h: 0.66, fontSize: 16, valign: "middle" });
    }

    const steps = [
      { n: "1", head: "Văn bản gốc", detail: "tin rao đúng như người bán viết", dark: false },
      { n: "2", head: "Chuỗi chỉ-để-dò", detail: "quy mọi biến thể về chữ số, kèm bản đồ vị trí ngược về văn bản gốc", dark: true },
      { n: "3", head: "Xoá đúng đoạn số", detail: "chỉ ký tự thuộc số điện thoại bị xoá, phần còn lại giữ nguyên", dark: false },
    ];
    steps.forEach((st, i) => {
      const x = 6.15 + i * 2.3, y = 1.95, w = 1.95, h = 2.15;
      box(s, x, y, w, h, st.dark ? C.ink : C.white, st.dark ? {} : { border: C.line });
      text(s, "BƯỚC " + st.n, { x: x + 0.18, y: y + 0.18, w: w - 0.3, h: 0.28, fontSize: 11, bold: true, color: st.dark ? C.terraOnDark : C.terra, charSpacing: 1 });
      text(s, st.head, { x: x + 0.18, y: y + 0.48, w: w - 0.3, h: 0.5, fontSize: 15, bold: true, color: st.dark ? C.white : C.ink });
      text(s, st.detail, { x: x + 0.18, y: y + 1.0, w: w - 0.32, h: 1.05, fontSize: 12, color: st.dark ? C.onDarkMuted : C.text });
      if (i < 2) line(s, x + w + 0.04, y + h / 2, x + 2.3 - 0.04, y + h / 2, { arrow: true, color: C.muted, width: 1.5 });
    });

    box(s, 6.15, 4.4, 3.2, 2.3, C.terraSoft);
    text(s, "14", { x: 6.45, y: 4.5, w: 2.6, h: 1.1, fontSize: 64, bold: true, color: C.terra });
    text(s, "kiểu nguỵ trang được phủ bằng test", { x: 6.45, y: 5.65, w: 2.7, h: 0.8, fontSize: 15 });
    box(s, 9.5, 4.4, 3.2, 2.3, C.mist);
    text(s, "0", { x: 9.8, y: 4.5, w: 2.6, h: 1.1, fontSize: 64, bold: true, color: C.ink });
    text(s, "số điện thoại sót lại trong kho thô", { x: 9.8, y: 5.65, w: 2.7, h: 0.8, fontSize: 15 });
    s.addNotes(
      "Tin rao hay chứa số điện thoại, và người bán cố tình né bộ lọc của sàn: chữ số Unicode, emoji, chữ cái thay số, số viết bằng chữ, hoặc ký tự vô hình chèn vào giữa.\n\n" +
      "Nếu chuẩn hoá rồi xoá thẳng trên chuỗi đã chuẩn hoá thì văn bản lưu lại bị méo. Nhóm tách hai việc: tạo một chuỗi chỉ dùng để dò, giữ bản đồ vị trí về văn bản gốc, rồi chỉ xoá đúng đoạn là số điện thoại trên văn bản gốc.\n\n" +
      "Việc xoá chạy ngay lúc ghi file, trước khi tin vào kho thô. Mười bốn kiểu nguỵ trang có test riêng, và quét lại kho thô không còn số nào."
    );
  }

  // 5 · Trích đặc trưng
  {
    const s = pres.addSlide();
    header(s, 5, "Đặc trưng từ văn bản", "Trích đặc trưng định lượng từ văn bản");
    text(s, [b("Bảy trường rút bằng regex. "), r("Ba luật khó nhất:")], { x: 0.6, y: 1.9, w: 12, h: 0.45, fontSize: 18 });
    text(s, "TIN RAO VIẾT", { x: 0.6, y: 2.48, w: 3, h: 0.3, fontSize: 11, bold: true, color: C.muted, charSpacing: 1 });
    text(s, "BỘ LUẬT HIỂU LÀ", { x: 4.45, y: 2.48, w: 3, h: 0.3, fontSize: 11, bold: true, color: C.muted, charSpacing: 1 });
    text(s, "VÌ SAO KHÓ", { x: 7.4, y: 2.48, w: 3, h: 0.3, fontSize: 11, bold: true, color: C.muted, charSpacing: 1 });
    const rules = [
      { quote: "“1 trệt 2 lầu”", size: 22, result: "3 tầng", why: [b("Đếm tầng bằng phép cộng. "), r("Tiếng Việt gọi tên từng thành phần: trệt + 2 lầu = 3 tầng.")] },
      { quote: "“4x15”", size: 24, result: "60 m² · mặt tiền 4 m", why: [b("Kích thước, không phải diện tích. "), r("Phải nhân ra, và chiều ngang chính là mặt tiền.")] },
      { quote: "“nhà mặt tiền”\n“mặt tiền 4m”", size: 17, result: "vị trí  ≠  số đo", why: [b("Cùng chữ, khác trường. "), r("Một cụm là loại vị trí, cụm kia là số đo mặt tiền.")] },
    ];
    rules.forEach((ru, i) => {
      const y = 2.85 + i * 1.35, h = 1.15;
      box(s, 0.6, y, 3.35, h, C.terraSoft);
      text(s, ru.quote, { x: 0.7, y, w: 3.15, h, fontSize: ru.size, bold: true, color: C.terra, align: "center", valign: "middle" });
      line(s, 4.0, y + h / 2, 4.4, y + h / 2, { arrow: true, color: C.muted, width: 1.5 });
      box(s, 4.45, y, 2.65, h, C.ink);
      text(s, ru.result, { x: 4.55, y, w: 2.45, h, fontSize: 18, bold: true, color: C.white, align: "center", valign: "middle" });
      text(s, ru.why, { x: 7.4, y, w: 5.3, h, fontSize: 16, valign: "middle" });
    });
    s.addNotes(
      "Từ mô tả, nhóm rút bảy trường định lượng bằng regex. Ba luật khó nhất đều đến từ cách người Việt viết tin rao.\n\n" +
      "Thứ nhất, \"1 trệt 2 lầu\" là 3 tầng. Phải cộng các thành phần, không lấy con số đầu tiên gặp được.\n\n" +
      "Thứ hai, \"4x15\" là kích thước chứ không phải diện tích. Phải nhân ra 60 m², và chiều ngang 4 m chính là mặt tiền.\n\n" +
      "Thứ ba, \"nhà mặt tiền\" là loại vị trí, còn \"mặt tiền 4m\" là số đo. Cùng một chữ nhưng đổ vào hai trường khác nhau."
    );
  }

  // 6 · Đo chất lượng
  {
    const s = pres.addSlide();
    header(s, 6, "Đặc trưng · Kiểm chứng", "Đo chất lượng bằng nhãn độc lập");
    box(s, 0.6, 1.95, 5.3, 2.2, C.mist);
    await iconCircle(s, "FaClipboardCheck", 0.9, 2.18, 0.6, C.white, C.ink2);
    text(s, "Nhãn không do LLM gán", { x: 1.7, y: 2.18, w: 4.0, h: 0.6, fontSize: 19, bold: true, color: C.ink, valign: "middle" });
    text(s, "Lấy từ chính trường có cấu trúc người bán điền vào form, thứ bộ luật regex không hề nhìn thấy.",
      { x: 0.9, y: 2.9, w: 4.8, h: 0.8, fontSize: 15 });
    text(s, "Bộ nhãn vàng: 200 tin ngẫu nhiên (seed 42) từ kho thô Chợ Tốt", { x: 0.9, y: 3.72, w: 4.8, h: 0.3, fontSize: 11.5, color: C.muted });

    box(s, 0.6, 4.35, 5.3, 2.35, C.terraSoft);
    text(s, "13/17", { x: 0.9, y: 4.5, w: 2.2, h: 0.85, fontSize: 44, bold: true, color: C.terra, valign: "middle" });
    text(s, "lỗi còn lại của trường số tầng lệch đúng 1 đơn vị", { x: 3.1, y: 4.5, w: 2.65, h: 0.85, fontSize: 15, bold: true, valign: "middle" });
    text(s, [r("Tin viết “1 trệt 1 lầu” nhưng điền số 1 vào form. "), b("Nhiễu của nhãn, không phải bộ luật đọc sai.")],
      { x: 0.9, y: 5.5, w: 4.8, h: 1.05, fontSize: 14 });

    text(s, "F1 theo trường", { x: 6.4, y: 1.95, w: 4, h: 0.4, fontSize: 17, bold: true, color: C.ink });
    const x0 = 8.35, span = 3.1, lo = 0.7, hi = 1.0;
    const px = (v) => x0 + span * (v - lo) / (hi - lo);
    const f1 = [["Diện tích", 0.939, "0,939 ✓"], ["Số phòng ngủ", 0.887, "0,887"], ["Số nhà tắm", 0.894, "0,894"], ["Số tầng", 0.802, "0,802"]];
    f1.forEach(([label, v, shown], i) => {
      const y = 2.75 + i * 0.75;
      text(s, label, { x: 6.4, y, w: 1.9, h: 0.5, fontSize: 15, valign: "middle" });
      box(s, x0, y, px(v) - x0, 0.5, v >= 0.9 ? C.green : C.ink2, { radius: 0.04 });
      text(s, shown, { x: 11.65, y, w: 1.1, h: 0.5, fontSize: 15, bold: true, color: v >= 0.9 ? C.green : C.ink, valign: "middle" });
    });
    line(s, x0, 5.7, x0 + span, 5.7, { color: C.line, width: 1 });
    [0.7, 0.8, 0.9, 1.0].forEach((v) => {
      line(s, px(v), 5.7, px(v), 5.78, { color: C.line, width: 1 });
      text(s, v.toFixed(2).replace(".", ","), { x: px(v) - 0.35, y: 5.8, w: 0.7, h: 0.28, fontSize: 11, color: C.muted, align: "center" });
    });
    line(s, px(0.9), 2.55, px(0.9), 5.7, { color: C.terra, width: 1.5, dash: "dash" });
    text(s, "chỉ tiêu 0,9", { x: px(0.9) - 0.6, y: 2.25, w: 1.2, h: 0.28, fontSize: 12, bold: true, color: C.terra, align: "center" });
    text(s, "Trục ngang bắt đầu từ 0,70 để thấy rõ khoảng cách tới chỉ tiêu.", { x: 6.4, y: 6.2, w: 6.3, h: 0.3, fontSize: 11, color: C.muted });
    s.addNotes(
      "Để đo bộ luật, nhóm không nhờ LLM gán nhãn. Nhãn lấy từ chính các trường có cấu trúc người bán điền vào form. Bộ luật chỉ đọc tiêu đề và mô tả nên không nhìn thấy các trường đó. Bộ nhãn vàng là 200 tin chọn ngẫu nhiên.\n\n" +
      "Diện tích đạt F1 0,939, vượt chỉ tiêu 0,9. Số tầng dừng ở 0,802.\n\n" +
      "Nhìn vào lỗi của số tầng: 13 trong 17 lỗi lệch đúng một đơn vị, phần lớn là tin viết \"1 trệt 1 lầu\" nhưng điền số 1 vào form. Cùng một cách viết, người này khai 1, người kia khai 2. Đó là nhiễu của nhãn, không phải bộ luật đọc sai.\n\n" +
      "Nếu được hỏi về phòng ngủ: F1 0,887, cũng chưa chạm 0,9 (thiếu 0,013); 12 trong 16 lỗi là lệch một đơn vị. Số nhà tắm không nằm trong chỉ tiêu."
    );
  }

  // 7 · Sáp nhập hành chính
  {
    const s = pres.addSlide();
    header(s, 7, "Địa chỉ", "Sáp nhập hành chính 2025");
    text(s, "168", { x: 0.6, y: 1.75, w: 3.5, h: 1.4, fontSize: 92, bold: true, color: C.ink, valign: "middle" });
    text(s, "đơn vị cấp xã của TP.HCM từ 01/07/2025", { x: 0.6, y: 3.15, w: 4.5, h: 0.7, fontSize: 17 });
    [["113 phường", 1.45], ["54 xã", 1.0], ["1 đặc khu", 1.3]].reduce((x, [label, w]) => {
      box(s, x, 3.9, w, 0.44, C.mist, { radius: 0.22 });
      text(s, label, { x, y: 3.9, w, h: 0.44, fontSize: 14, bold: true, color: C.ink, align: "center", valign: "middle" });
      return x + w + 0.12;
    }, 0.6);
    box(s, 0.6, 4.75, 4.5, 1.95, C.terraSoft);
    text(s, "Cùng một khu, hai cái tên", { x: 0.9, y: 4.95, w: 4.0, h: 0.4, fontSize: 17, bold: true, color: C.terra });
    text(s, "Tin 2026 ghi phường mới, dữ liệu lịch sử ghi phường cũ.", { x: 0.9, y: 5.45, w: 4.0, h: 1.0, fontSize: 16 });

    text(s, "Bảng ánh xạ dựng từ chính dữ liệu", { x: 5.6, y: 1.9, w: 7, h: 0.45, fontSize: 18, bold: true, color: C.ink });
    box(s, 5.6, 2.5, 2.0, 1.3, C.white, { border: C.line });
    s.addImage({ data: await icon("FaFileLines", C.ink2), x: 5.82, y: 2.68, w: 0.34, h: 0.34 });
    text(s, "1 tin Chợ Tốt", { x: 5.82, y: 3.1, w: 1.7, h: 0.5, fontSize: 15, bold: true, color: C.ink });
    line(s, 7.64, 3.15, 8.0, 3.15, { arrow: true, width: 1.5 });
    box(s, 8.05, 2.5, 2.35, 1.3, C.mist);
    text(s, "API TRẢ CẢ HAI", { x: 8.25, y: 2.6, w: 2.0, h: 0.28, fontSize: 10.5, bold: true, color: C.muted, charSpacing: 1 });
    text(s, "tên phường hệ cũ\ntên phường hệ mới", { x: 8.25, y: 2.92, w: 2.05, h: 0.75, fontSize: 14 });
    line(s, 10.44, 3.15, 10.8, 3.15, { arrow: true, width: 1.5 });
    box(s, 10.85, 2.5, 1.85, 1.3, C.ink);
    text(s, "1 cặp ánh xạ", { x: 11.0, y: 2.65, w: 1.6, h: 0.45, fontSize: 15, bold: true, color: C.white });
    text(s, "do sàn khẳng định", { x: 11.0, y: 3.1, w: 1.6, h: 0.5, fontSize: 12, color: C.onDarkMuted });

    ["Phường cũ A", "Phường cũ B", "Phường cũ C"].forEach((label, i) => {
      const y = 4.25 + i * 0.68;
      box(s, 5.6, y, 1.6, 0.5, C.mist);
      text(s, label, { x: 5.6, y, w: 1.6, h: 0.5, fontSize: 13, align: "center", valign: "middle" });
      line(s, 7.22, y + 0.25, 7.8, 5.19, { color: C.muted, width: 1.25 });
    });
    box(s, 7.82, 4.79, 1.65, 0.8, C.ink2);
    text(s, "Phường mới X", { x: 7.82, y: 4.79, w: 1.65, h: 0.8, fontSize: 14, bold: true, color: C.white, align: "center", valign: "middle" });
    text(s, "Minh hoạ: nhiều phường cũ gộp vào một phường mới", { x: 5.6, y: 6.35, w: 4.0, h: 0.3, fontSize: 11, color: C.muted });

    box(s, 9.85, 4.25, 2.85, 1.12, C.terraSoft);
    text(s, "14/16", { x: 10.05, y: 4.3, w: 2.5, h: 0.55, fontSize: 30, bold: true, color: C.terra });
    text(s, "phường mới gộp từ nhiều phường cũ", { x: 10.05, y: 4.83, w: 2.55, h: 0.5, fontSize: 12.5 });
    box(s, 9.85, 5.5, 2.85, 1.2, C.terraSoft);
    text(s, "0,45", { x: 10.05, y: 5.55, w: 2.5, h: 0.55, fontSize: 30, bold: true, color: C.terra });
    text(s, "tỷ lệ đa số thấp nhất: phường cũ đông tin nhất chỉ chiếm 45%", { x: 10.05, y: 6.08, w: 2.55, h: 0.6, fontSize: 12 });
    s.addNotes(
      "Từ 01/07/2025, TP.HCM còn 168 đơn vị cấp xã: 113 phường, 54 xã và 1 đặc khu. Hệ quả cho dữ liệu: tin 2026 ghi tên phường mới, còn bộ lịch sử ghi tên phường cũ.\n\n" +
      "Thay vì tải một bảng ánh xạ bên ngoài, nhóm dựng bảng từ chính dữ liệu. API Chợ Tốt trả cả tên phường hệ cũ lẫn hệ mới cho cùng một tin, nên mỗi tin là một cặp ánh xạ do sàn khẳng định.\n\n" +
      "Bảng này cũng lộ ra cạm bẫy: 14 trong 16 phường mới gộp từ nhiều phường cũ. Tỷ lệ đa số thấp nhất chỉ 0,45, nghĩa là với phường mới đó, phường cũ xuất hiện nhiều nhất cũng chỉ chiếm 45% số tin. Ánh xạ kiểu này bị đánh dấu là đa số mỏng thay vì áp thẳng."
    );
  }

  // 8 · Chống rò rỉ nhãn
  {
    const s = pres.addSlide();
    header(s, 8, "Chống rò rỉ nhãn", "Chống rò rỉ nhãn: kiểm, không tin");
    s.addImage({ data: await icon("FaListCheck", C.terra), x: 0.6, y: 1.98, w: 0.38, h: 0.38 });
    text(s, [r("Danh sách kiểm chạy trước "), b("mỗi"), r(" lần huấn luyện. Nó bắt được hai lỗi thật:")],
      { x: 1.15, y: 1.9, w: 11.5, h: 0.55, fontSize: 18, valign: "middle" });
    const bugs = [
      { tag: "Lỗi 1", title: "Bước tách từ tái tạo cụm tiền", from: "5,85 tỷ", via: "bỏ dấu phẩy", to: "“585” + “tỷ”",
        body: "Tiền đã lọc khỏi mô tả, nhưng bỏ dấu phẩy thập phân biến “5,85” thành “585” nằm cạnh chữ “tỷ” còn sót." },
      { tag: "Lỗi 2", title: "Đơn giá lọt qua bộ lọc tiền", from: "110 triệum2", via: "× diện tích", to: "= nhãn",
        body: "Đơn giá dính chữ nên lọt qua dưới dạng “110 triệum2”; nhân với diện tích ra thẳng giá cần dự báo." },
    ];
    bugs.forEach((bug, i) => {
      const x = 0.6 + i * 6.15, y = 2.65, w = 5.95;
      box(s, x, y, w, 3.0, C.white, { border: C.line, shadow: true });
      box(s, x + 0.3, y + 0.3, 0.9, 0.34, C.terra, { radius: 0.17 });
      text(s, bug.tag, { x: x + 0.3, y: y + 0.3, w: 0.9, h: 0.34, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle" });
      text(s, bug.title, { x: x + 0.3, y: y + 0.78, w: w - 0.6, h: 0.45, fontSize: 18, bold: true, color: C.ink });
      box(s, x + 0.3, y + 1.35, 2.2, 0.65, C.mist);
      text(s, bug.from, { x: x + 0.3, y: y + 1.35, w: 2.2, h: 0.65, fontSize: 19, bold: true, color: C.ink, align: "center", valign: "middle" });
      text(s, bug.via, { x: x + 2.5, y: y + 1.26, w: 1.0, h: 0.3, fontSize: 11, color: C.muted, align: "center" });
      line(s, x + 2.6, y + 1.68, x + 3.4, y + 1.68, { arrow: true, width: 1.5 });
      box(s, x + 3.5, y + 1.35, 2.15, 0.65, C.terraSoft);
      text(s, bug.to, { x: x + 3.5, y: y + 1.35, w: 2.15, h: 0.65, fontSize: 19, bold: true, color: C.terra, align: "center", valign: "middle" });
      text(s, bug.body, { x: x + 0.3, y: y + 2.22, w: w - 0.6, h: 0.7, fontSize: 14 });
    });
    box(s, 0.6, 5.9, 12.1, 0.9, C.ink);
    text(s, "0 / 34.607", { x: 0.95, y: 5.9, w: 3.2, h: 0.9, fontSize: 34, bold: true, color: C.white, valign: "middle" });
    text(s, "dòng mang token tiền vào TF-IDF", { x: 3.75, y: 5.9, w: 8.4, h: 0.9, fontSize: 19, color: C.onDarkMuted, valign: "middle" });
    s.addNotes(
      "Rò rỉ nhãn là lỗi làm kết quả đẹp giả. Nhóm không tin vào câu \"đã lọc rồi\", mà chạy một danh sách kiểm trước mỗi lần huấn luyện. Danh sách này bắt được hai lỗi thật.\n\n" +
      "Lỗi một: tiền đã được lọc khỏi mô tả, nhưng bước tách từ bỏ dấu phẩy thập phân, biến \"5,85\" thành \"585\" nằm cạnh chữ \"tỷ\" còn sót. Giá quay lại trong đặc trưng.\n\n" +
      "Lỗi hai: đơn giá viết dính thành \"110 triệum2\" nên lọt bộ lọc tiền. Nhân với diện tích là ra thẳng nhãn.\n\n" +
      "Sau khi sửa, không dòng nào trong 34.607 dòng còn token tiền đi vào TF-IDF."
    );
  }

  // 9 · Pipeline (vẽ lại: hình 01-pipeline-tong-the.png là bản kế hoạch cũ)
  {
    const s = pres.addSlide();
    header(s, 9, "Tổng quan", "Pipeline tổng thể");
    const stages = [
      ["FaSpider", "Thu thập", ["Chợ Tốt: API JSON", "mogi.vn: HTML", "HF: parquet"]],
      ["FaBoxArchive", "Kho thô", ["Ghi JSONL", "Xoá SĐT lúc ghi", "Khử trùng mã tin"]],
      ["FaFilter", "Tiền xử lý", ["Chuẩn hoá giá", "Chuẩn hoá địa chỉ", "Regex: 7 trường", "Khử trùng lặp", "Lọc ngoại lai"]],
      ["FaGears", "Đặc trưng", ["Tách từ tiếng Việt", "Cờ văn bản", "TF-IDF/SVD", "ColumnTransformer"]],
      ["FaCubes", "Mô hình", ["12 mô hình, 4 tầng", "Học trên log(giá)", "Kiểm rò rỉ nhãn"]],
      ["FaChartColumn", "Đánh giá, demo", ["E1, E2, E3, ablation", "Web app Streamlit"]],
    ];
    for (const [i, [ic, name, items]] of stages.entries()) {
      const x = 0.6 + i * 2.04, y = 1.95, w = 1.9, last = i === stages.length - 1;
      box(s, x, y, w, 3.3, last ? C.ink : C.mist);
      s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.46, h: 0.46, fill: { color: C.terra }, line: { color: C.terra, width: 0 } });
      text(s, String(i + 1), { x: x + 0.2, y: y + 0.22, w: 0.46, h: 0.46, fontSize: 14, bold: true, color: C.white, align: "center", valign: "middle" });
      s.addImage({ data: await icon(ic, last ? C.terraOnDark : C.ink2), x: x + w - 0.6, y: y + 0.27, w: 0.36, h: 0.36 });
      text(s, name, { x: x + 0.2, y: y + 0.85, w: w - 0.3, h: 0.45, fontSize: 16, bold: true, color: last ? C.white : C.ink });
      text(s, items.map((t, k) => ({ text: t, options: { bullet: { indent: 11 }, breakLine: k < items.length - 1 } })),
        { x: x + 0.14, y: y + 1.38, w: w - 0.24, h: 1.8, fontSize: 12.5, color: last ? C.onDarkMuted : C.text, paraSpaceAfter: 5 });
    }
    text(s, "Số dòng qua từng bước làm sạch", { x: 0.6, y: 5.45, w: 6, h: 0.38, fontSize: 15, bold: true, color: C.ink });
    const funnel = [["42.760", "Gộp ba nguồn"], ["41.997", "Đủ giá, diện tích"], ["38.370", "Miền hợp lệ, bỏ tin thuê"], ["35.617", "Khử trùng lặp"], ["34.607", "Lọc IQR giá/m²"]];
    funnel.forEach(([num, label], i) => {
      const x = 0.6 + i * 2.475, y = 5.92, w = 2.2, last = i === funnel.length - 1;
      box(s, x, y, w, 0.88, last ? C.terra : C.mist);
      text(s, num, { x, y: y + 0.06, w, h: 0.45, fontSize: 21, bold: true, color: last ? C.white : C.ink, align: "center", valign: "middle" });
      text(s, label, { x, y: y + 0.5, w, h: 0.3, fontSize: 11.5, color: last ? C.white : C.muted, align: "center" });
      if (!last) line(s, x + w + 0.04, y + 0.44, x + 2.475 - 0.04, y + 0.44, { arrow: true, width: 1.25 });
    });
    s.addNotes(
      "Đây là toàn bộ pipeline, sáu khối từ trái sang phải.\n\n" +
      "Thu thập từ ba nguồn, ghi vào kho thô, xoá số điện thoại ngay lúc ghi. Tiền xử lý chuẩn hoá giá và địa chỉ, trích bảy trường bằng regex, khử trùng lặp và lọc ngoại lai. " +
      "Khối đặc trưng tách từ tiếng Việt, thêm cờ văn bản và TF-IDF/SVD, ghép với đặc trưng bảng bằng ColumnTransformer. Sau đó huấn luyện 12 mô hình, kiểm rò rỉ trước mỗi lần chạy, rồi đánh giá bằng bốn thí nghiệm và đưa lên web app.\n\n" +
      "Hàng dưới là số dòng qua từng bước làm sạch: gộp ba nguồn được 42.760 dòng, còn 34.607 dòng sau khi lọc ngoại lai."
    );
  }

  // 10 · Danh mục mô hình
  {
    const s = pres.addSlide();
    header(s, 10, "Mô hình", "Danh mục 12 mô hình, 4 tầng");
    s.addShape(pres.shapes.ISOSCELES_TRIANGLE ?? "triangle", { x: 0.6, y: 1.85, w: 7.3, h: 0.55, fill: { color: C.terra }, line: { color: C.terra, width: 0 } });
    const floors = [
      { tier: "Tầng 3", role: "mở rộng", models: ["KNN", "Cây quyết định", "MLP"] },
      { tier: "Tầng 2", role: "chủ lực", models: ["Random Forest", "LightGBM", "CatBoost", "XGBoost"], dark: true },
      { tier: "Tầng 1", role: "tuyến tính", models: ["Linear", "Ridge", "Lasso"] },
      { tier: "Tầng 0", role: "mốc", models: ["Dummy", "Trung vị giá/m² theo nhóm"], highlight: "Trung vị giá/m² theo nhóm" },
    ];
    floors.forEach((f, i) => {
      const y = 2.48 + i * 1.08;
      box(s, 0.6, y, 7.3, 0.98, f.dark ? C.ink : C.mist, { square: true });
      text(s, f.tier, { x: 0.85, y: y + 0.14, w: 1.8, h: 0.4, fontSize: 17, bold: true, color: f.dark ? C.white : C.ink });
      text(s, f.role, { x: 0.85, y: y + 0.52, w: 1.8, h: 0.32, fontSize: 13, color: f.dark ? C.onDarkMuted : C.muted });
      f.models.reduce((x, m) => {
        const w = 0.34 + m.length * 0.095;
        const hot = m === f.highlight;
        box(s, x, y + 0.26, w, 0.46, hot ? C.terra : (f.dark ? C.ink2 : C.white), { radius: 0.23 });
        text(s, m, { x, y: y + 0.26, w, h: 0.46, fontSize: 14, bold: hot || f.dark, color: hot || f.dark ? C.white : C.text, align: "center", valign: "middle" });
        return x + w + 0.1;
      }, 2.7);
    });

    box(s, 8.35, 1.95, 4.35, 4.85, C.white, { border: C.line, shadow: true });
    await iconCircle(s, "FaUserTie", 8.65, 2.2, 0.72, C.terraSoft, C.terra);
    text(s, "Baseline môi giới", { x: 8.65, y: 3.05, w: 3.8, h: 0.45, fontSize: 20, bold: true, color: C.ink });
    text(s, "Trung vị giá/m² theo (quận, phường, loại nhà) nhân diện tích: cách một người môi giới định giá trong đầu.",
      { x: 8.65, y: 3.55, w: 3.8, h: 1.25, fontSize: 15 });
    box(s, 8.65, 4.9, 3.75, 0.8, C.mist);
    text(s, [b("Thắng Dummy: "), r("chỉ chứng minh dữ liệu có tín hiệu.")], { x: 8.8, y: 4.9, w: 3.5, h: 0.8, fontSize: 14, valign: "middle" });
    box(s, 8.65, 5.82, 3.75, 0.8, C.terraSoft);
    text(s, [b("Thắng baseline môi giới: ", { color: C.terra }), r("mới là phần học máy đóng góp.")], { x: 8.8, y: 5.82, w: 3.5, h: 0.8, fontSize: 14, valign: "middle" });
    s.addNotes(
      "Nhóm so 12 mô hình, chia bốn tầng như bốn tầng nhà.\n\n" +
      "Tầng 0 là mốc: Dummy dự báo trung vị, và baseline môi giới. Tầng 1 là tuyến tính: Linear, Ridge, Lasso. Tầng 2 là nhóm chủ lực: Random Forest và ba mô hình boosting. Tầng 3 là KNN, cây quyết định và MLP.\n\n" +
      "Mốc đáng quan tâm nhất là baseline môi giới: lấy trung vị giá/m² theo quận, phường, loại nhà rồi nhân diện tích. Đó đúng là cách một người môi giới ước giá trong đầu.\n\n" +
      "Thắng Dummy chỉ cho biết dữ liệu có tín hiệu. Thắng baseline môi giới mới là phần học máy thật sự đóng góp."
    );
  }

  // 11 · Kết quả E1
  {
    const s = pres.addSlide();
    header(s, 11, "Kết quả · E1", "Kết quả chính (E1)");
    text(s, "2.326 tin Chợ Tốt · 5-fold · mỗi ô là trung bình qua 5 fold, MdAPE kèm độ lệch chuẩn", { x: 0.6, y: 1.72, w: 12, h: 0.35, fontSize: 14, color: C.muted });
    const head = ["Mô hình", "MdAPE (%)", "RMSE (tỷ)", "R²"];
    const data = [
      ["Dummy (trung vị)", "34,6 ± 2,1", "7,250", "-0,053"],
      ["Trung vị giá/m² theo nhóm", "20,5 ± 1,4", "3,802", "0,706"],
      ["Ridge", "19,7 ± 0,7", "7,002", "-0,160"],
      ["Random Forest", "15,1 ± 0,9", "4,626", "0,579"],
      ["CatBoost", "14,2 ± 1,2", "3,857", "0,708", true],
      ["LightGBM", "13,9 ± 1,2", "3,925", "0,698", true],
      ["XGBoost", "14,0 ± 1,1", "3,793", "0,716", true],
    ];
    const rows = [head.map((h, k) => ({ text: h, options: { bold: true, color: C.white, fill: { color: C.ink }, align: k ? "right" : "left", valign: "middle" } }))];
    data.forEach(([name, ...vals]) => {
      const lead = vals[3] === true;
      const cells = [name, ...vals.slice(0, 3)].map((v, k) => ({
        text: v,
        options: { bold: lead, color: lead ? C.ink : C.text, fill: { color: lead ? C.terraSoft : C.white }, align: k ? "right" : "left", valign: "middle" },
      }));
      rows.push(cells);
    });
    s.addTable(rows, { x: 0.6, y: 2.2, w: 7.6, colW: [3.1, 1.7, 1.4, 1.4], rowH: 0.49, fontFace: FONT, fontSize: 15, border: { type: "solid", pt: 0.75, color: C.line } });
    text(s, "Ba dòng tô màu cách nhau chưa tới một độ lệch chuẩn giữa các fold, nên bảng không chọn ra một mô hình thắng.",
      { x: 0.6, y: 6.3, w: 7.6, h: 0.55, fontSize: 13, color: C.muted });

    box(s, 8.6, 2.2, 4.1, 2.15, C.ink);
    text(s, "6,32–6,66", { x: 8.9, y: 2.38, w: 3.6, h: 0.8, fontSize: 42, bold: true, color: C.white, valign: "middle" });
    text(s, "điểm phần trăm MdAPE mà nhóm dẫn đầu thấp hơn baseline môi giới", { x: 8.9, y: 3.25, w: 3.55, h: 0.9, fontSize: 15, color: C.onDarkMuted });
    box(s, 8.6, 4.55, 4.1, 2.2, C.mist);
    s.addImage({ data: await icon("FaScaleBalanced", C.ink2), x: 8.9, y: 4.78, w: 0.36, h: 0.36 });
    text(s, "So sánh công bằng", { x: 9.38, y: 4.74, w: 3.1, h: 0.44, fontSize: 17, bold: true, color: C.ink, valign: "middle" });
    text(s, "Cùng bộ fold, cùng ngân sách tinh chỉnh, cùng seed. Không tuyên bố hơn kém khi hai khoảng trung bình ± độ lệch chuẩn chồng lấn.",
      { x: 8.9, y: 5.3, w: 3.6, h: 1.3, fontSize: 14 });
    s.addNotes(
      "Kết quả chính trên 2.326 tin Chợ Tốt, 5-fold. Mọi mô hình dùng chung một bộ fold, cùng ngân sách tinh chỉnh (tối đa 20 cấu hình), cùng seed.\n\n" +
      "Nhóm dẫn đầu là CatBoost, LightGBM và XGBoost, MdAPE quanh 14%. So với baseline môi giới 20,5%, nhóm này thấp hơn 6,32 tới 6,66 điểm phần trăm. Đó là phần giá trị học máy tạo ra so với cách định giá thủ công.\n\n" +
      "Ba mô hình này cách nhau chưa tới một độ lệch chuẩn giữa các fold, nên nhóm không tuyên bố mô hình nào thắng.\n\n" +
      "Nếu được hỏi: tinh chỉnh chạy một lần trên toàn phần train rồi dùng lại cho 5 fold (không nested), nên số CV hơi lạc quan. Trên tập hold-out 20% chưa dùng để chọn tham số: XGBoost 13,4%, CatBoost 13,8%, LightGBM 14,2%."
    );
  }

  // 12 · Vì sao báo cả ba chỉ số
  {
    const s = pres.addSlide();
    header(s, 12, "Kết quả · Cách đọc", "Vì sao phải báo cả ba chỉ số");
    text(s, [r("Nhóm tuyến tính: "), b("MdAPE khá"), r(", nhưng "), b("R² âm", { color: C.terra }), r(".")], { x: 0.6, y: 1.8, w: 12, h: 0.55, fontSize: 22, valign: "middle" });
    const hd = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.ink }, align: "center", valign: "middle" } });
    const lbl = (t) => ({ text: t, options: { bold: true, color: C.ink, fill: { color: C.mist }, valign: "middle" } });
    const val = (t, bad) => ({ text: t, options: { bold: !!bad, color: bad ? C.terra : C.text, align: "center", valign: "middle", fill: { color: C.white } } });
    s.addTable([
      [hd(""), hd("Hồi quy tuyến tính"), hd("Ridge"), hd("LightGBM")],
      [lbl("MdAPE (%)"), val("18,8"), val("19,7"), val("13,9")],
      [lbl("RMSE (tỷ)"), val("10,970\n± 10,006", true), val("7,002\n± 2,962"), val("3,925\n± 1,125")],
      [lbl("R²"), val("-2,783", true), val("-0,160", true), val("0,698")],
    ], { x: 0.6, y: 2.55, w: 6.2, colW: [1.55, 1.75, 1.45, 1.45], rowH: [0.62, 0.5, 0.8, 0.5], fontFace: FONT, fontSize: 15, border: { type: "solid", pt: 0.75, color: C.line } });
    text(s, "Trung bình 5-fold trên 2.326 tin Chợ Tốt (bảng E1)", { x: 0.6, y: 5.13, w: 6.2, h: 0.3, fontSize: 11.5, color: C.muted });

    const flow = ["Huấn luyện trên log(giá)", "Vài điểm ngoại suy rất xa", "exp phóng đại thành sai số khổng lồ trên thang VND", "RMSE sụp, trung vị không đổi"];
    flow.forEach((t, i) => {
      const y = 2.55 + i * 0.64, last = i === flow.length - 1;
      box(s, 7.2, y, 5.5, 0.54, last ? C.terraSoft : C.mist);
      s.addShape(pres.shapes.OVAL, { x: 7.33, y: y + 0.09, w: 0.36, h: 0.36, fill: { color: last ? C.terra : C.ink2 }, line: { width: 0, color: C.ink2 } });
      text(s, String(i + 1), { x: 7.33, y: y + 0.09, w: 0.36, h: 0.36, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle" });
      text(s, t, { x: 7.85, y, w: 4.75, h: 0.54, fontSize: 15, bold: last, color: last ? C.terra : C.text, valign: "middle" });
    });
    text(s, "Không phải lỗi cài đặt: đó là cơ chế của phép biến đổi log.", { x: 7.2, y: 5.05, w: 5.5, h: 0.3, fontSize: 12.5, italic: true, color: C.muted });

    const verdicts = [
      [b("Đọc R² một mình"), r(" → kết luận hồi quy tuyến tính vô dụng. "), b("Sai.", { color: C.terra })],
      [b("Đọc MdAPE một mình"), r(" → kết luận nó ngang boosting. "), b("Cũng sai.", { color: C.terra })],
    ];
    for (const [i, runs] of verdicts.entries()) {
      const x = 0.6 + i * 6.15;
      box(s, x, 5.55, 5.95, 1.2, C.terraSoft);
      await iconCircle(s, "FaXmark", x + 0.28, 5.84, 0.62, C.white, C.terra);
      text(s, runs, { x: x + 1.1, y: 5.55, w: 4.65, h: 1.2, fontSize: 16, valign: "middle" });
    }
    s.addNotes(
      "Bảng E1 có một chỗ lạ: nhóm tuyến tính có MdAPE khá, quanh 19%, nhưng R² lại âm.\n\n" +
      "Đây không phải lỗi cài đặt. Mô hình học trên log giá. Ở vài điểm nó ngoại suy rất xa, và khi lấy exp để quy về VND thì sai lệch đó thành con số khổng lồ. RMSE, kéo theo R², sụp vì vài điểm này, còn trung vị gần như không đổi. " +
      "Nhìn RMSE của hồi quy tuyến tính: độ lệch chuẩn giữa các fold 10,006, gần bằng chính trung bình 10,970.\n\n" +
      "Vì vậy phải đọc cả ba chỉ số. Chỉ đọc R² thì tưởng hồi quy tuyến tính vô dụng. Chỉ đọc MdAPE thì tưởng nó ngang boosting. Cả hai đều sai."
    );
  }

  // 13 · Ablation
  {
    const s = pres.addSlide();
    header(s, 13, "Kết quả · Ablation", "Ablation: văn bản đáng bao nhiêu?");
    text(s, "ĐẶC TRƯNG DÙNG", { x: 0.85, y: 1.95, w: 3, h: 0.3, fontSize: 11, bold: true, color: C.muted, charSpacing: 1 });
    text(s, "MDAPE (%)", { x: 4.2, y: 1.95, w: 1.3, h: 0.3, fontSize: 11, bold: true, color: C.muted, align: "right", charSpacing: 1 });
    text(s, "Δ SO VỚI CHỈ BẢNG", { x: 5.9, y: 1.95, w: 3, h: 0.3, fontSize: 11, bold: true, color: C.muted, charSpacing: 1 });
    const abl = [["Chỉ đặc trưng bảng", "14,77", 0], ["Bảng + cờ văn bản thủ công", "14,08", -0.69], ["Bảng + TF-IDF/SVD", "13,91", -0.86], ["Bảng + TF-IDF/SVD + cờ", "13,88", -0.89]];
    abl.forEach(([label, mdape, d], i) => {
      const y = 2.4 + i * 0.95, last = i === abl.length - 1;
      box(s, 0.6, y, 8.4, 0.8, last ? C.terraSoft : C.mist);
      text(s, label, { x: 0.85, y, w: 3.3, h: 0.8, fontSize: 16, bold: last, color: last ? C.ink : C.text, valign: "middle" });
      text(s, mdape, { x: 4.2, y, w: 1.3, h: 0.8, fontSize: 19, bold: true, color: C.ink, align: "right", valign: "middle" });
      if (d === 0) {
        text(s, "0,00 (mốc)", { x: 5.9, y, w: 2, h: 0.8, fontSize: 15, color: C.muted, valign: "middle" });
      } else {
        const bw = 2.3 * Math.abs(d) / 0.89;
        box(s, 5.9, y + 0.22, bw, 0.36, C.terra, { radius: 0.04 });
        text(s, d.toFixed(2).replace(".", ","), { x: 5.9 + bw + 0.1, y, w: 0.85, h: 0.8, fontSize: 16, bold: true, color: C.terra, valign: "middle" });
      }
    });
    box(s, 9.35, 2.4, 3.35, 2.3, C.ink);
    text(s, "-0,89", { x: 9.65, y: 2.55, w: 2.9, h: 1.0, fontSize: 50, bold: true, color: C.white, valign: "middle" });
    text(s, [r("điểm % MdAPE khi thêm", { breakLine: true }), r("TF-IDF/SVD và cờ văn bản")], { x: 9.65, y: 3.6, w: 2.9, h: 0.9, fontSize: 14.5, color: C.onDarkMuted });
    box(s, 9.35, 4.9, 3.35, 1.15, C.mist);
    text(s, "Cùng bộ fold, cùng mô hình (LightGBM), cùng ngân sách. Khác biệt duy nhất là nhánh văn bản.",
      { x: 9.55, y: 4.9, w: 3.0, h: 1.15, fontSize: 13, valign: "middle" });
    text(s, [b("Đọc đúng cỡ hiệu ứng: "), r("độ lệch chuẩn giữa các fold tới 1,19, lớn hơn mức giảm. Bốn cấu hình dùng chung bộ fold nên đây là phép so bắt cặp: một xu hướng nhất quán về dấu, chưa phải con số chốt.")],
      { x: 0.6, y: 6.2, w: 12.1, h: 0.6, fontSize: 13, color: C.muted });
    s.addNotes(
      "Quay lại câu hỏi ở đầu: văn bản đáng bao nhiêu. Nhóm giữ nguyên mô hình LightGBM, bộ fold và ngân sách tinh chỉnh, chỉ bật tắt nhánh văn bản.\n\n" +
      "Chỉ đặc trưng bảng cho MdAPE 14,77%. Thêm cờ văn bản thủ công giảm 0,69 điểm. Thêm TF-IDF/SVD giảm 0,86. Dùng cả hai giảm 0,89. Cả ba cấu hình có văn bản đều tốt hơn, và tốt hơn theo cùng một chiều.\n\n" +
      "Nhóm cũng nói rõ cỡ hiệu ứng: mức giảm nhỏ hơn độ lệch chuẩn giữa các fold, lên tới 1,19. Vì bốn cấu hình dùng chung fold nên đây là phép so bắt cặp, vẫn có ý nghĩa, nhưng nên đọc là xu hướng nhất quán về dấu, chưa phải con số chốt."
    );
  }

  // 14 · E2
  {
    const s = pres.addSlide();
    header(s, 14, "Kết quả · E2", "E2: trôi giá theo thời gian");
    box(s, 0.6, 1.95, 4.5, 1.3, C.mist);
    text(s, "HUẤN LUYỆN", { x: 0.9, y: 2.08, w: 3, h: 0.28, fontSize: 11, bold: true, color: C.terra, charSpacing: 1 });
    text(s, "Tin ≤ 06/2025", { x: 0.9, y: 2.36, w: 4, h: 0.45, fontSize: 21, bold: true, color: C.ink });
    text(s, "31.947 tin, bộ lịch sử", { x: 0.9, y: 2.82, w: 4, h: 0.3, fontSize: 13, color: C.muted });
    line(s, 2.85, 3.29, 2.85, 3.66, { arrow: true, width: 1.5 });
    box(s, 0.6, 3.7, 4.5, 1.3, C.ink);
    text(s, "KIỂM TRA", { x: 0.9, y: 3.83, w: 3, h: 0.28, fontSize: 11, bold: true, color: C.terraOnDark, charSpacing: 1 });
    text(s, "Tin crawl 08/2026", { x: 0.9, y: 4.11, w: 4, h: 0.45, fontSize: 21, bold: true, color: C.white });
    text(s, "2.326 tin Chợ Tốt", { x: 0.9, y: 4.57, w: 4, h: 0.3, fontSize: 13, color: C.onDarkMuted });
    box(s, 0.6, 5.2, 4.5, 1.55, C.terraSoft);
    text(s, "+2,8", { x: 0.85, y: 5.3, w: 1.55, h: 0.75, fontSize: 38, bold: true, color: C.terra, valign: "middle" });
    text(s, "điểm % MdAPE: trung vị mức xấu đi khi chuyển giao", { x: 2.4, y: 5.3, w: 2.55, h: 0.75, fontSize: 13, bold: true, valign: "middle" });
    text(s, "CatBoost +0,8 · LightGBM +2,4 · XGBoost +3,1", { x: 0.85, y: 6.15, w: 4.1, h: 0.4, fontSize: 13, color: C.text });

    s.addImage({ path: path.join(ROOT, "reports/figures/eda-04-gia-m2-theo-thang.png"), altText: "Giá/m² trung vị theo tháng ở năm quận", x: 5.5, y: 1.95, w: 7.2, h: 3.0 });
    box(s, 5.5, 5.2, 3.5, 1.55, C.mist);
    s.addImage({ data: await icon("FaCircleCheck", C.green), x: 5.72, y: 5.38, w: 0.32, h: 0.32 });
    text(s, [b("Cả hai phía đều là giá rao"), r(", nên không lẫn khoảng cách giá rao / giá giao dịch.")], { x: 6.15, y: 5.32, w: 2.72, h: 1.35, fontSize: 13 });
    box(s, 9.2, 5.2, 3.5, 1.55, C.terraSoft);
    s.addImage({ data: await icon("FaTriangleExclamation", C.terra), x: 9.42, y: 5.38, w: 0.32, h: 0.32 });
    text(s, [b("Nhưng hai phía khác sàn"), r(": một phần chênh lệch là chênh giữa hai nguồn, không phải trôi giá thuần tuý.")], { x: 9.85, y: 5.32, w: 2.72, h: 1.35, fontSize: 13 });
    s.addNotes(
      "E2 hỏi: mô hình học trên dữ liệu cũ đem dùng cho thị trường hôm nay thì sai số ra sao.\n\n" +
      "Nhóm huấn luyện trên 31.947 tin đăng tới 30/06/2025, rồi kiểm trên 2.326 tin crawl tháng 08/2026. Cả hai phía đều là giá rao, nên con số đo được không lẫn khoảng cách giữa giá rao và giá giao dịch.\n\n" +
      "Kết quả: mọi mô hình tính được đều xấu đi, trung vị 2,8 điểm phần trăm MdAPE. Trong nhóm boosting, CatBoost chỉ tăng 0,8 điểm.\n\n" +
      "Có một lưu ý nhóm muốn nói trước: tập huấn luyện và tập kiểm còn khác nhau về sàn, nên một phần chênh lệch là chênh giữa hai nguồn chứ không thuần là trôi giá.\n\n" +
      "Biểu đồ bên phải là bối cảnh: giá/m² trung vị theo tháng ở năm quận, điểm tròn là bộ lịch sử, hình thoi là tin crawl 08/2026.\n\n" +
      "Nếu được hỏi về hồi quy tuyến tính: dự báo tràn số khi chuyển giao. Ridge cũng tuyến tính nhưng có điều chuẩn thì chuyển giao bình thường."
    );
  }

  // 15 · Demo
  {
    const s = pres.addSlide();
    header(s, 15, "Sản phẩm", "Demo: web app dự báo có giải thích");
    box(s, 0.6, 1.9, 8.5, 4.24, C.white, { border: C.line, shadow: true, square: true });
    s.addImage({ path: path.join(ROOT, "submission/Demo/demo-02-ket-qua-va-giai-thich.png"), altText: "Ảnh chụp web app: kết quả dự báo và biểu đồ SHAP waterfall", x: 0.6, y: 1.9, w: 8.5, h: 4.24 });
    text(s, "Ví dụ trong ảnh: nhà phố Tân Bình, 60 m², 3 tầng → giá ước lượng 8,04 tỷ, khoảng tham khảo 6,90–9,19 tỷ.",
      { x: 0.6, y: 6.25, w: 8.5, h: 0.5, fontSize: 13, color: C.muted });
    const points = [
      ["Streamlit", "nạp đúng artefact mà bước huấn luyện xuất ra"],
      ["Khoảng tham khảo", "rộng bằng MdAPE đo trên\nhold-out (14,2%), không\nphải con số tự đặt"],
      ["Giải thích từng ca", "SHAP waterfall cho biết đặc trưng nào đẩy giá lên, đặc trưng nào kéo xuống"],
    ];
    points.forEach(([head, detail], i) => {
      const y = 1.9 + i * 1.45;
      s.addShape(pres.shapes.OVAL, { x: 9.45, y, w: 0.46, h: 0.46, fill: { color: C.terra }, line: { color: C.terra, width: 0 } });
      text(s, String(i + 1), { x: 9.45, y, w: 0.46, h: 0.46, fontSize: 14, bold: true, color: C.white, align: "center", valign: "middle" });
      text(s, head, { x: 10.05, y: y + 0.02, w: 2.65, h: 0.42, fontSize: 17, bold: true, color: C.ink, valign: "middle" });
      text(s, detail, { x: 10.05, y: y + 0.48, w: 2.65, h: 0.9, fontSize: 13.5 });
    });
    s.addNotes(
      "Đây là web app Streamlit. Người dùng nhập quận, phường, loại nhà, diện tích, số tầng, số phòng và mô tả tin rao.\n\n" +
      "App nạp đúng artefact mà bước huấn luyện xuất ra, không huấn luyện lại. Ví dụ trong ảnh là nhà phố Tân Bình 60 m², 3 tầng: giá ước lượng 8,04 tỷ.\n\n" +
      "Khoảng tham khảo 6,90 tới 9,19 tỷ rộng đúng bằng MdAPE đo trên tập hold-out, 14,2%, chứ không phải con số nhóm tự đặt.\n\n" +
      "Bên phải là biểu đồ SHAP waterfall, giải thích cho riêng căn này đặc trưng nào đẩy giá lên, đặc trưng nào kéo xuống.\n\n" +
      "Nếu có thời gian, mở app chạy trực tiếp: make demo."
    );
  }

  // 16 · Hạn chế
  {
    const s = pres.addSlide();
    header(s, 16, "Tổng kết", "Hạn chế, nói thẳng");
    const limits = [
      ["FaTag", "Học từ giá rao, không phải giá giao dịch", "Nhóm không có dữ liệu để đo khoảng cách đó nên không phỏng đoán."],
      ["FaMapLocationDot", "Chỉ phủ TP.HCM, dày nhất ở ba quận mục tiêu", "E3 đo trực tiếp mức suy giảm khi sang phường chưa thấy: MdAPE trung bình 15,2% ± 4,1."],
      ["FaNotEqual", "Tin rao tự mâu thuẫn", "Form một đằng, mô tả một nẻo. Những tin này nằm ngoài tầm với của mọi bộ luật văn bản."],
      ["FaStairs", "Số tầng chưa đạt chỉ tiêu F1 0,9", "Báo cáo trung thực kèm phân tích lỗi, thay vì chỉnh luật cho khớp nhãn nhiễu."],
    ];
    for (const [i, [ic, head, body]] of limits.entries()) {
      const x = 0.6 + (i % 2) * 6.15, y = 1.95 + Math.floor(i / 2) * 2.45, w = 5.95;
      box(s, x, y, w, 2.25, C.mist);
      await iconCircle(s, ic, x + 0.32, y + 0.32, 0.66, C.terra, C.white);
      text(s, head, { x: x + 1.2, y: y + 0.25, w: w - 1.45, h: 0.8, fontSize: 18, bold: true, color: C.ink, valign: "middle" });
      text(s, body, { x: x + 0.32, y: y + 1.2, w: w - 0.64, h: 0.9, fontSize: 15 });
    }
    s.addNotes(
      "Nhóm nói thẳng bốn hạn chế.\n\n" +
      "Một, mô hình học từ giá rao, không phải giá giao dịch. Nhóm không có dữ liệu giao dịch nên không đoán khoảng cách giữa hai loại giá.\n\n" +
      "Hai, dữ liệu chỉ phủ TP.HCM và dày nhất ở Tân Bình, Tân Phú, Quận 12. E3 bỏ từng phường ra khỏi tập huấn luyện rồi dự báo đúng phường đó: MdAPE trung bình 15,2%, dao động từ 11,8% tới 21,4% tuỳ phường.\n\n" +
      "Ba, tin rao tự mâu thuẫn: form một đằng, mô tả một nẻo.\n\n" +
      "Bốn, trường số tầng chưa đạt F1 0,9. Nhóm báo cáo kèm phân tích lỗi thay vì chỉnh luật cho khớp một tập nhãn tự nó đã nhiễu."
    );
  }

  // 17 · Hướng phát triển
  {
    const s = pres.addSlide();
    header(s, 17, "Tổng kết", "Hướng phát triển");
    const next = [
      ["FaDatabase", "Bổ sung dữ liệu", "Crawl script đã resume được, chỉ cần chạy tiếp"],
      ["FaLocationCrosshairs", "Toạ độ và đặc trưng khoảng cách", "Đã thiết kế, hoãn theo cut-line"],
      ["FaHandshake", "Đối chiếu với giá giao dịch thật", "Nếu tiếp cận được dữ liệu giao dịch"],
      ["FaChartLine", "Đọc đường cong học", "Cho biết crawl thêm còn đáng hay không"],
    ];
    for (const [i, [ic, head, detail]] of next.entries()) {
      const y = 1.95 + i * 1.2;
      await iconCircle(s, ic, 0.6, y + 0.1, 0.75, C.mist, C.ink2);
      text(s, head, { x: 1.6, y: y + 0.05, w: 5.2, h: 0.42, fontSize: 18, bold: true, color: C.ink });
      text(s, detail, { x: 1.6, y: y + 0.48, w: 5.2, h: 0.42, fontSize: 15, color: C.muted });
    }
    box(s, 7.2, 1.95, 5.5, 4.85, C.white, { border: C.line, shadow: true });
    text(s, "Đường cong học (LightGBM)", { x: 7.45, y: 2.1, w: 5.0, h: 0.38, fontSize: 16, bold: true, color: C.ink });
    text(s, "MdAPE (%) trên cùng tập hold-out, theo số tin huấn luyện", { x: 7.45, y: 2.47, w: 5.0, h: 0.3, fontSize: 12, color: C.muted });
    s.addChart(pres.charts.LINE, [{ name: "MdAPE (%)", labels: ["186", "465", "744", "1.023", "1.302", "1.581", "1.860"], values: [22.9, 15.7, 15.3, 15.5, 14.2, 13.4, 14.2] }], {
      x: 7.35, y: 2.8, w: 5.2, h: 2.95,
      chartColors: [C.terra], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 8,
      valAxisMinVal: 12, valAxisMaxVal: 24, valAxisMajorUnit: 4, valAxisLabelFormatCode: "0",
      valAxisLabelColor: C.muted, catAxisLabelColor: C.muted, valAxisLabelFontSize: 11, catAxisLabelFontSize: 11,
      valAxisLabelFontFace: FONT, catAxisLabelFontFace: FONT,
      valGridLine: { color: "E3EAEC", size: 0.75 }, catGridLine: { style: "none" },
      showLegend: false, showTitle: false,
    });
    text(s, "186 → 1.860 tin: MdAPE 22,9% → 14,2%. Bước cuối tăng 0,8 điểm; mỗi tỷ lệ mới chạy một lần nên chưa kết luận được đường cong đã phẳng.",
      { x: 7.45, y: 5.8, w: 5.05, h: 0.9, fontSize: 12.5 });
    s.addNotes(
      "Hướng tiếp theo có bốn việc.\n\n" +
      "Bổ sung dữ liệu: script crawl đã chạy tiếp được từ chỗ dừng, chỉ cần chạy thêm.\n\n" +
      "Thêm toạ độ và đặc trưng khoảng cách: đã thiết kế, hoãn lại theo cut-line của kế hoạch.\n\n" +
      "Đối chiếu với giá giao dịch thật, nếu tiếp cận được dữ liệu.\n\n" +
      "Và đọc đường cong học để quyết định crawl thêm có đáng không. Từ 186 lên 1.860 tin, MdAPE giảm từ 22,9% xuống 14,2%. Bước cuối lại tăng 0,8 điểm, nhưng mỗi tỷ lệ mới chạy một lần, nên muốn chốt đường cong đã phẳng thì phải lặp lại nhiều lần rồi so trung bình."
    );
  }

  // 18 · Kết luận, hỏi đáp
  {
    const s = pres.addSlide();
    s.background = { color: C.ink };
    text(s, "KẾT LUẬN", { x: 0.7, y: 0.85, w: 5, h: 0.4, fontSize: 13, bold: true, color: C.terraOnDark, charSpacing: 1.5 });
    text(s, "Ba điều nhóm rút ra", { x: 0.7, y: 1.3, w: 7, h: 0.8, fontSize: 38, bold: true, color: C.white });
    const takeaways = [
      [b("Boosting hơn baseline môi giới 6,32–6,66 điểm %", { color: C.white }), r(" MdAPE. Giá trị của học máy nằm ở khoảng cách này.", { color: C.onDarkMuted })],
      [b("Mô tả rao vặt có tín hiệu giá", { color: C.white }), r(": giảm 0,89 điểm % MdAPE, nhất quán về dấu nhưng nhỏ hơn độ lệch giữa các fold.", { color: C.onDarkMuted })],
      [b("Dữ liệu cũ mất độ chính xác theo thời gian", { color: C.white }), r(": chuyển sang tin 2026, MdAPE xấu đi trung vị 2,8 điểm %.", { color: C.onDarkMuted })],
    ];
    takeaways.forEach((runs, i) => {
      const y = 2.45 + i * 1.4;
      text(s, String(i + 1), { x: 0.7, y, w: 0.6, h: 1.1, fontSize: 34, bold: true, color: C.terraOnDark });
      text(s, runs, { x: 1.4, y: y + 0.08, w: 6.3, h: 1.15, fontSize: 17 });
    });
    box(s, 8.35, 0.85, 4.35, 5.9, C.inkSoft, { radius: 0.12 });
    text(s, "Cảm ơn thầy cô và các bạn đã lắng nghe", { x: 8.75, y: 1.4, w: 3.6, h: 1.8, fontSize: 26, bold: true, color: C.white });
    text(s, "Hỏi đáp", { x: 8.75, y: 3.6, w: 3.6, h: 1.0, fontSize: 48, bold: true, color: C.terraOnDark });
    text(s, "CS106.F31.CN2 · Nhóm 14", { x: 8.75, y: 6.05, w: 3.6, h: 0.4, fontSize: 13, color: C.onDarkMuted });
    s.addNotes(
      "Nhóm rút ra ba điều.\n\n" +
      "Một, nhóm boosting hơn baseline môi giới 6,32 tới 6,66 điểm phần trăm MdAPE.\n\n" +
      "Hai, mô tả rao vặt có tín hiệu giá, nhưng hiệu ứng nhỏ: 0,89 điểm.\n\n" +
      "Ba, mô hình học trên dữ liệu cũ kém đi khi gặp thị trường mới, trung vị 2,8 điểm.\n\n" +
      "Nhóm cảm ơn thầy cô và các bạn đã lắng nghe. Xin mời đặt câu hỏi."
    );
  }

  await pres.writeFile({ fileName: OUT });
  console.log("Xong:", OUT);
}

main().catch((err) => { console.error(err); process.exit(1); });
