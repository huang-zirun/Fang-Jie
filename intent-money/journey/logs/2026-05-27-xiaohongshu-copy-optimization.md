# 2026-05-27 小红书文案语境优化

## 修改内容

### 问题
当用户选择小红书平台时，任务详情页和数据回填页显示的文案不符合小红书语境（如"分镜脚本"、"口播文案"、"播放量"等）。

### 解决方案
前端根据 `platform_name` 动态切换文案，小红书平台显示更贴合的语境词汇。

### 具体修改

#### TaskDetail.vue
1. **"分镜脚本"** → 小红书显示 **"图文脚本"**
2. **"口播文案"** → 小红书显示 **"笔记正文"**
3. **提示语"标题和文案已可复制"** → 小红书显示 **"标题和正文已可复制"**

#### DataReport.vue
4. **"播放量"** → 小红书显示 **"阅读量"**（包括标签、placeholder、提示语）

### 实现方式
- 添加 Vue computed 属性：`storyboardTitle`, `scriptTitle`, `copyHintText`, `playCountLabel`
- 根据 `task.value?.platform_name?.includes('小红书')` 判断平台类型
- 抖音等其他平台保持原有文案不变

### 修改文件
- `frontend/src/views/TaskDetail.vue`
- `frontend/src/views/DataReport.vue`
