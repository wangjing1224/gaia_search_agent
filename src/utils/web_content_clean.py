import re
import unicodedata

def clean_web_markdown_content(content: str) -> str:
    """
    【全能优化版】网页Markdown内容清洗函数
    
    功能：
    1. 针对 Wikipedia：精准去除目录、多语言列表、工具条、参考文献跳转。
    2. 针对 通用网页：去除广告、登录注册、ICP备案、Cookie提示、HTML残留、页脚版权。
    3. 文本规范化：统一全角半角、中英文空格、去重标点。
    """
    # 空值/非字符串防护
    if not isinstance(content, str) or not content.strip():
        return ""

    # ==========================
    # Phase 1: 预处理 - 基础规范化
    # ==========================
    # 统一换行符、去除不可见字符
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = re.sub(r'[\u200b\u200c\u200d\u0009\u00a0]', ' ', content)

    # ==========================
    # Phase 2: 批量删除已知的垃圾块（块级清理）
    # ==========================
    # 1. [通用] 过滤 Jina/系统 截断提示
    content = re.sub(r'SYSTEM NOTICE:[\s\S]*?$', '', content)
    
    # 2. [Wiki专用] 过滤 Contents 目录块（从Contents开始到第一个非列表行结束）
    # 这种结构只在 Wiki 类网站出现，不会误伤普通网页的正文
    content = re.sub(r'Contents\n[\s\S]*?\n(?=[A-Za-z]+[^\*\-•])', '', content, flags=re.I)
    
    # 3. [Wiki专用] 过滤工具条文本
    content = re.sub(r'Tools Actions\n[\s\S]*?\n(?=[A-Z]+)', '', content)
    
    # 4. [通用] 过滤常见的脚本/样式代码块残留
    content = re.sub(r'<script[\s\S]*?</script>', '', content, flags=re.I)
    content = re.sub(r'<style[\s\S]*?</style>', '', content, flags=re.I)

    # ==========================
    # Phase 3: 逐行精细化清洗
    # ==========================
    lines = content.split('\n')
    cleaned_lines = []
    
    # 合并垃圾关键词：Wiki专用 + 通用网页
    garbage_patterns = [
        # --- Wiki 类关键词 ---
        "jump to", "toggle", "main menu", "sidebar", "navigation", 
        "create account", "log in", "personal tools", "contribute",
        "recent changes", "upload file", "special pages", "appearance",
        "print/export", "download as pdf", "in other projects", 
        "wikimedia commons", "wikibooks", "wikiquote", "view source",
        "view history", "what links here", "related changes", "permanent link",
        "page information", "cite this page", "edit links", "donate",
        "wikipedia, the free encyclopedia", "from wikipedia", "redirects here",
        "tools actions", "read general", "get shortened url", 
        "download qr code", "printable version", "wikiversity", 
        "wikidata item", "glossary", "v t e", "part of a series on",
        
        # --- 通用网页关键词 (CN/EN) ---
        "cookie", "privacy policy", "terms of use", "advertisement",
        "隐私政策", "用户协议", "广告", "推广", "扫码", "关注公众号",
        "登录", "注册", "充值", "会员", "客服", "联系我们", "免责声明",
        "版权所有", "保留所有权利", "copyright", "all rights reserved",
        "京ICP备", "粤ICP备", "备案号", "公网安备",
        "返回顶部", "上一页", "下一页", "首页", "末页", "页码", "top of page",
        "powered by", "designed by", "技术支持", "友情链接", "广告投放",
        "share this", "follow us", "subscribe", "newsletter",
        
        # --- API/工具残留 ---
        "jina", "aliyun", "百炼", "api", "request id", "response time",
        "token usage", "rate limit", "content-type", "charset=utf-8"
    ]
    
    # 定义非中英文的语言列表特征（处理 Wiki 多语言列表）
    non_cn_en_pattern = re.compile(r'^[^\u4e00-\u9fa5a-zA-Z0-9\s]+$')
    
    # 定义目录列表项特征 (1.1, 2.1.2)
    catalog_pattern = re.compile(r'^\*\s*(\d+(\.\d+)*|[a-zA-Z]+(\.\d+)*)\s')

    skip_mode = False
    
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # 跳过空行
        if not line_stripped:
            continue

        # 1. 关键词过滤
        is_garbage = False
        for pattern in garbage_patterns:
            if pattern in line_lower:
                is_garbage = True
                break
        if is_garbage:
            continue

        # 2. 过滤目录索引 (Wiki/文档通用)
        if catalog_pattern.match(line_stripped):
            continue

        # 3. 过滤多语言/无意义列表项 (Wiki + 通用Footer)
        if line_stripped.startswith(('*', '-', '•')):
            # 特征1：纯小语种字符（无中英）
            content_part = line_stripped.lstrip('* -•').strip()
            if non_cn_en_pattern.match(content_part):
                continue
            # 特征2：短语言名/短链接（长度<20，无实际内容）
            if len(content_part) < 20 and not any(char.isalpha() and char.islower() for char in content_part):
                continue
            # 特征3：特定语言标记
            if any(marker in line_stripped for marker in ['/', '་', 'অ', 'ܐ', 'ע', 'ಕ', 'བ', '한국어', '日本語', '粵語', '吴语']):
                continue

        # 4. 过滤菜单勾选行 (Markdown Checkbox)
        if line_stripped.startswith(('- [x]', '- [ ]')):
            continue

        # 5. 过滤过短的行（非标题类，长度<8且不含字母/中文）
        # 这能过滤掉很多页码、符号、分隔符
        if len(line_stripped) < 8 and not re.search(r'[a-zA-Z\u4e00-\u9fa5]', line_stripped):
            continue

        # 6. 保留有效行
        cleaned_lines.append(line_stripped)

    content = "\n".join(cleaned_lines)

    # ==========================
    # Phase 4: 正则深度清洗 (HTML + Markdown)
    # ==========================
    # 1. 去除 Markdown 图片 ![alt](url)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    
    # 2. [关键] 去除链接，只留文本 [text](url) -> text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    
    # 3. 去除引用标记/脚注
    content = re.sub(r'\[\d+\]|\[\d+\.\d+\]|\[[a-z]\]|\[(edit|citation needed|引用|来源)\]', '', content)
    
    # 4. [通用] 去除 HTML 标签残留 (Jina 爬取通用网页时常见)
    content = re.sub(r'<[^>]+>', '', content)
    
    # 5. [通用] 去除多余的 Markdown 表格线 (可选，如果不想保留表格结构)
    # 这里的逻辑是去除单纯的分割线，保留数据行
    # content = re.sub(r'\|[-=]+(\|[-=]+)+\|?', '', content)
    
    # 6. 去除代码块标记 (保留代码内容，只去 ```)
    content = re.sub(r'```', '', content) 

    # 7. 去除连续的特殊符号/标点 (如 "------", ".......")
    content = re.sub(r'[-=*_]{3,}', '', content)
    content = re.sub(r'([，。！？；：、,.!?;:\s]){2,}', r'\1', content)

    # 8. 压缩多余空行
    content = re.sub(r'\n{2,}', '\n', content)

    # ==========================
    # Phase 5: 最终规范化
    # ==========================
    content = unicodedata.normalize('NFKC', content)
    
    # 去除中英文间多余空格 (排版优化)
    content = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', content)
    content = re.sub(r'([a-zA-Z0-9])\s+([\u4e00-\u9fa5])', r'\1 \2', content)
    content = re.sub(r'([\u4e00-\u9fa5])\s+([a-zA-Z0-9])', r'\1 \2', content)
    
    return content.strip()


# ------------------------------
# 测试：使用你提供的实际爬取内容
# ------------------------------
if __name__ == "__main__":
    # 粘贴你提供的爬取内容到这里
    test_content = """
Title Artificial intelligence
URL Source https://en.wikipedia.org/wiki/Artificial_intelligence
Published Time 2001-10-08T16:55:49Z
Markdown Content
Artificial intelligence - Wikipedia
* Main page
* Contents
* Current events
* Random article
* About Wikipedia
* Contact us
* Help
* Learn to edit
* Community portal
Search
Contents
* (Top) * 1.1 Reasoning and problem-solving * 1.2 Knowledge representation * 1.3 Planning and decision-making * 1.4 Learning * 1.5 Natural language processing * 1.6 
Perception * 1.7 Social intelligence * 1.8 General intelligence * 2.1 Search and optimization * 2.1.1 State space search * 2.1.2 Local search * 2.2 Logic * 2.3 Probabilistic methods for uncertain reasoning * 2.4 Classifiers and statistical learning methods * 2.5 Artificial neural networks * 2.6 Deep learning * 2.7 GPT * 2.8 Hardware and software * 3.1 Health and medicine * 3.2 Gaming * 3.3 Mathematics * 3.4 Finance * 3.5 Military * 3.6 Generative AI * 3.7 Agents * 3.8 Web search * 3.9 Sexuality * 3.10 Other industry-specific tasks * 4.1 Risks and harm * 4.1.1 Privacy and copyright * 4.1.2 Dominance by tech giants * 4.1.3 Power needs and environmental impacts * 4.1.4 Misinformation * 4.1.5 Algorithmic bias and fairness * 4.1.6 Lack of transparency * 4.1.7 Bad actors and weaponized AI * 4.1.8 Technological unemployment * 4.1.9 Existential risk * 4.2 Ethical machines and alignment * 4.3 Open source * 4.4 Frameworks * 4.5 Regulation
* 5 History * 6.1 Defining artificial intelligence * 6.1.1 Legal definitions * 6.2 Evaluating approaches to AI * 6.2.1 Symbolic AI and its limits * 6.2.2 Neat vs scruffy * 6.2.3 Soft vs hard computing * 6.2.4 Narrow vs general AI * 6.3 Machine consciousness sentience and mind * 6.3.1 Consciousness * 6.3.2 Computationalism and functionalism * 6.3.3 AI welfare and rights * 7.1 Superintelligence and the singularity * 7.2 Transhumanism
* 8 In fiction
* 9 See also
* 10 Explanatory notes * 11.1 Textbooks * 11.2 History of AI * 11.3 Other sources
* 12 External links
Artificial intelligence
* Afrikaans
* Alemannisch
* አማርኛ
* अंगिका
* العربية
* Aragonés
* Արեւմտահայերէն
* অসমীয়া
* Asturianu
* Avañe'ẽ
* Azərbaycanca
* تۆرکجه
* বাংলা
* 閩南語 / Bân-lâm-gí
* Башҡортса
* Беларуская
* Беларуская (тарашкевіца)")
* भोजपुरी
* Bikol Central
* Български
* Boarisch
* བོད་ཡིག
* Bosanski
* Brezhoneg
* Буряад
* Català
* Чӑвашла
* Cebuano
* Čeština
* Cymraeg
* Dansk
* الدارجة
* Deutsch
* Eesti
* Ελληνικά
* Español
* Esperanto
* Estremeñu
* Euskara
* فارسی
* Fiji Hindi
* Français
* Furlan
* Gaeilge
* Gaelg
* Gàidhlig
* Galego
* 贛語
* Gĩkũyũ
* गोंयची कोंकणी / Gõychi Konknni
* 한국어
* Hausa
* Հայերեն
* हिन्दी
* Hrvatski
* Ido
* Igbo
* Ilokano
* Bahasa Indonesia
* Interlingua
* Interlingue
* IsiZulu
* Íslenska
* Italiano
* עברית
* Jawa
* ಕನ್ನಡ
* ქართული
* کٲشُر
* Қазақша
* Kiswahili
* Kreyòl ayisyen
* Kriyòl gwiyannen
* Kurdî
* Кыргызча
* ລາວ
* Latina
* Latviešu
* Lëtzebuergesch
* Lietuvių
* Ligure
* Limburgs
* La.lojban
* Lombard
* Magyar
* Madhurâ
* Македонски
* Malagasy
* മലയാളം
* Malti
* मराठी
* მარგალური
* مصرى
* Bahasa Melayu
* Minangkabau
* Монгол
* မြန်မာဘာသာ
* Nederlands
* Nedersaksies
* नेपाली
* नेपाल भाषा
* 日本語
* Nordfriisk
* Norsk bokmål
* Norsk nynorsk
* Occitan
* ଓଡ଼ିଆ
* Oʻzbekcha / ўзбекча
* ਪੰਜਾਬੀ
* پنجابی
* ပအိုဝ်ႏဘာႏသာႏ
* پښتو
* Patois
* ភាសាខ្មែរ
* Picard
* Piemontèis
* Plattdüütsch
* Polski
* Português
* Qaraqalpaqsha
* Qırımtatarca
* Reo tahiti
* Ripoarisch
* Română
* Runa Simi
* Русиньскый
* Русский
* Саха тыла
* संस्कृतम्
* Sängö
* Scots
* Sesotho sa Leboa
* Shqip
* Sicilianu
* සිංහල
* Simple English
* سنڌي
* Slovenčina
* Slovenščina
* کوردی
* Српски / srpski
* Srpskohrvatski / српскохрватски
* Suomi
* Svenska
* Tagalog
* தமிழ்
* Татарча / tatarça
* తెలుగు
* ไทย
* Тоҷикӣ
* Türkçe
* Türkmençe
* Українська
* اردو
* ئۇيغۇرچە / Uyghurche
* Vèneto
* Tiếng Việt
* Võro
* Walon
* 文言
* Winaray
* 吴语
* ייִדיש
* 粵語
* Zazaki
* Žemaitėška
* 中文
* Betawi
* Kadazandusun
* Fɔ̀ngbè
* Jaku Iban
* ꠍꠤꠟꠐꠤ
* ⵜⴰⵎⴰⵣⵉⵖⵜ ⵜⴰⵏⴰⵡⴰⵢⵜ
* Article
* Talk
* Read
You can view its source ")
Tools Actions
* Read General
* Get shortened URL
* Download QR code
* Printable version
* Wikiversity
* Wikidata item
Intelligence of machines
Part of a series on
* Artificial general intelligence
* Intelligent agent
* Recursive self-improvement
* Planning
* Computer vision
* General game playing
* Knowledge representation
* Natural language processing
* Robotics
* AI safety
Approaches
* Machine learning
* Symbolic
* Deep learning
* Bayesian networks
* Evolutionary algorithms
* Hybrid intelligent systems
* Systems integration
* Open-source
* AI data centers
* Bioinformatics
* Deepfake
* Earth sciences
* Finance
* Generative AI * Art * Audio * Music
* Government
* Healthcare * Mental health
* Industry
* Software development
* Translation
* Military
* Physics
* Projects
* AI alignment
* Artificial consciousness
* The bitter lesson
* Chinese room
* Friendly AI
* Ethics
* Existential risk
* Turing test
* Uncanny valley
* Human–AI interaction
* Timeline
* Progress
* AI winter
* AI boom
* AI bubble
* Deepfake pornography * Taylor Swift deepfake pornography controversy * Grok deepfake pornography controversy#Sexual_deepfake_and_illegal_content_generation_on_X "Grok (chatbot)")
* Google Gemini image generation controversy
* Pause Giant AI Experiments
* Removal of Sam Altman from OpenAI
* Statement on AI Risk
* Tay (chatbot) "Tay (chatbot)")
* _Théâtre D'opéra Spatial_
* Voiceverse NFT plagiarism scandal
Glossary
* Glossary
* v
* t
* e
**Artificial intelligence** (**AI**) is the capability of computational systems to perform tasks typically associated with human intelligence such as learning reasoning problem-solving perception and decision-making It is a field of research in computer science that develops and studies methods and software that enable machines 
to perceive their environment and use learning and intelligence to take actions that maximize their chances of achieving defined goals.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-FOOTNOTERussellNorvig20211%E2%80%934-1)
High-profile applications of AI include advanced web search engines (e.g Google Search) recommendation systems (used by YouTube Amazon "Amazon (company)") and Netflix) virtual assistants (e.g Google Assistant Siri and Alexa) autonomous vehicles (e.g Waymo) generative and creative tools (e.g language models and AI art) and superhuman play and analysis in strategy games (e.g chess and Go "Go (game)")) However many AI applications are not perceived as AI "A lot of cutting edge AI has filtered 
into general applications often without being called AI because once something becomes useful enough and common enough it's not labeled AI anymore."[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-2)[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-3)
Various subfields of AI research are centered around particular goals and the use of particular tools The traditional goals of AI research include learning reasoning knowledge representation planning natural language processing perception and support for robotics.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-Problems_of_AI-4) To reach these goals AI researchers have adapted and integrated a wide range of techniques including search and mathematical optimization formal logic artificial neural networks and methods based on statistics operations research and economics.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-Tools_of_AI-5) AI also draws upon psychology linguistics philosophy neuroscience and other fields.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-6) Some companies such as OpenAI Google DeepMind and Meta,[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-7) aim to create artificial general intelligence (AGI) – AI that can complete virtually any cognitive task at least as well as a human
Goals
The general problem of simulating (or creating) intelligence has been broken into subproblems These consist of particular traits or capabilities that researchers expect an intelligent system to display The traits described below have received the most attention and cover the scope of AI research.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-Problems_of_AI-4)
### Reasoning and problem-solving
Early researchers developed algorithms that imitated step-by-step reasoning that humans use when they solve puzzles or make logical deductions.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-15) By the late 1980s and 1990s methods were developed for dealing with uncertain or incomplete information employing concepts from probability and economics.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-16)
Many of these algorithms are insufficient for solving large reasoning problems because they experience a "combinatorial explosion" They become exponentially slower as the problems grow.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-Intractability_and_efficiency_and_the_combinatorial_explosion-17) Even humans 
rarely use the step-by-step deduction that early AI research could model They solve most of their problems using fast intuitive judgments.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-Psychological_evidence_of_the_prevalence_of_sub-18) Accurate and efficient reasoning is an unsolved problem
### Knowledge representation
An ontology represents knowledge as a set of concepts within a domain and the relationships between those concepts
A knowledge base is a body of knowledge represented in a form that can be used by a program An ontology "Ontology (information science)") is the set of objects relations concepts and properties used by a particular domain of knowledge.[](https://en.wikipedia.org/wiki/Artificial_intelligence#cite_note-FOOTNOTERussellNorvig2021272-25) Knowledge bases need to represent things such as objects properties categories and relations between
SYSTEM NOTICE: Content truncated.This is page 1 of 23.
To read the next page, please call this tool again with page_number=2.
Or you can set page_number to a specific page number to read that page directly.
    """
    
    cleaned_content = clean_web_markdown_content(test_content)
    print("===== 清洗后的核心内容 =====")
    print(cleaned_content)