# 双语支持功能说明

## 概述

击剑AI智能体平台现已支持中英文双语切换功能，用户可以在中文和英文之间自由切换界面语言。

## 实现的功能

### 1. 后端国际化支持

- **模块位置**: `utils/i18n.py`
- **功能**: 
  - 加载和管理翻译文件
  - 支持嵌套键（如 `app.title`）
  - 提供翻译API接口

### 2. 前端国际化支持

- **模块位置**: `static/js/i18n.js`
- **功能**:
  - 自动加载翻译文件
  - 更新页面所有文本
  - 语言切换按钮
  - 本地存储语言偏好

### 3. 语言包文件

- **中文**: `locales/zh_CN.json`
- **英文**: `locales/en_US.json`
- **内容**: 包含所有界面文本的翻译

### 4. API端点

- `GET /api/translations?lang=zh_CN` - 获取指定语言的翻译
- `POST /api/set_language` - 设置当前语言

## 使用方法

### 用户操作

1. **切换语言**: 点击页面右上角的语言切换按钮
2. **自动保存**: 语言选择会自动保存到本地存储
3. **即时生效**: 切换后页面文本立即更新

### 开发者使用

#### 后端使用i18n

```python
from utils.i18n import i18n

# 设置语言
i18n.set_language('en_US')

# 获取翻译
title = i18n.t('app.title')  # 返回 "Fencing AI Platform"
```

#### 前端使用i18n

```javascript
// 获取翻译
const title = window.i18n.t('app.title');

// 切换语言
window.i18n.setLanguage('en_US');
```

#### HTML中使用

```html
<!-- 使用data-i18n属性 -->
<h1 data-i18n="app.title">击剑AI智能体平台</h1>

<!-- 使用data-i18n-placeholder属性 -->
<input data-i18n-placeholder="video.placeholder" placeholder="...">
```

## 已翻译的界面元素

### 主要区域
- ✅ 页面标题和导航
- ✅ 视频播放区域
- ✅ AI聊天区域
- ✅ 弹幕控制区域
- ✅ 动作分析面板
- ✅ 知识推荐区域
- ✅ FIE数据区域
- ✅ 知识卡片
- ✅ 时间轴标注
- ✅ 互动问答

### 动态内容
- ✅ 通知消息
- ✅ 错误提示
- ✅ 成功提示
- ✅ 加载状态

## 添加新翻译

### 步骤

1. **在语言包文件中添加键值对**

`locales/zh_CN.json`:
```json
{
  "new_section": {
    "title": "新标题",
    "description": "新描述"
  }
}
```

`locales/en_US.json`:
```json
{
  "new_section": {
    "title": "New Title",
    "description": "New Description"
  }
}
```

2. **在HTML中使用**

```html
<h2 data-i18n="new_section.title">新标题</h2>
<p data-i18n="new_section.description">新描述</p>
```

3. **在JavaScript中使用**

```javascript
const title = window.i18n.t('new_section.title');
```

## 技术细节

### 翻译键命名规范

- 使用点号分隔的层级结构：`section.subsection.key`
- 使用小写字母和下划线：`action_analysis.title`
- 保持语义清晰：`chat.welcome_message`

### 翻译文件结构

```json
{
  "section": {
    "subsection": {
      "key": "value"
    }
  }
}
```

### 语言代码

- `zh_CN`: 简体中文
- `en_US`: 美式英语

## 未来扩展

### 计划支持的语言
- [ ] 繁体中文 (zh_TW)
- [ ] 日语 (ja_JP)
- [ ] 法语 (fr_FR)
- [ ] 德语 (de_DE)

### 功能增强
- [ ] 根据浏览器语言自动检测
- [ ] 支持RTL语言（阿拉伯语、希伯来语）
- [ ] 日期和时间格式本地化
- [ ] 数字格式本地化

## 注意事项

1. **翻译完整性**: 确保所有语言包包含相同的键
2. **文本长度**: 不同语言的文本长度可能不同，注意UI布局
3. **文化差异**: 某些表达可能需要根据文化背景调整
4. **动态内容**: AI生成的内容目前不支持自动翻译

## 测试

### 测试语言切换

1. 打开应用
2. 点击语言切换按钮
3. 检查所有文本是否正确更新
4. 刷新页面，确认语言设置已保存

### 测试翻译完整性

```bash
# 检查翻译文件格式
python3 -c "import json; json.load(open('locales/zh_CN.json'))"
python3 -c "import json; json.load(open('locales/en_US.json'))"
```

## 常见问题

**Q: 切换语言后某些文本没有更新？**
A: 检查该元素是否有 `data-i18n` 属性，或确保JavaScript代码使用了 `window.i18n.t()` 方法。

**Q: 如何添加新的翻译键？**
A: 在两个语言包文件中同时添加相同的键，然后在代码中使用。

**Q: 翻译文件加载失败怎么办？**
A: 检查文件路径和JSON格式，确保文件编码为UTF-8。

## 更新日志

- **2024-01-XX**: 初始版本，支持中英文双语切换
- 实现了完整的i18n系统
- 添加了语言切换按钮
- 更新了所有主要界面元素

