# InvalidCharacterError 错误修复 - 2026-05-22

## 问题描述

前端出现错误：
```
InvalidCharacterError: Failed to execute 'setAttribute' on 'Element': '0' is not a valid attribute name.
```

## 根因分析

错误发生在 `DataReport.vue` 中 `van-field` 组件的 `:rules` 属性。当传入数组 `[{ required: true, message: '...' }]` 时：

1. **Vant 组件未设置 `inheritAttrs: false`**：`van-field` 组件和其内部的 `Cell` 组件都没有设置 `inheritAttrs: false`
2. **Auto-import 解析问题**：`unplugin-vue-components` 的 `VantResolver` 可能未正确识别 `rules` 为已声明 prop
3. **属性泄漏**：未消费的 prop 进入 `$attrs`，最终被透传到原生 `<div>` 元素
4. **数组键成为属性名**：Vue 遍历数组时 `Object.keys([{...}])` 返回 `['0']`，尝试在 DOM 元素上设置属性名 `'0'`，触发浏览器 `InvalidCharacterError`

### 技术细节

Vant Field 组件源码 (`node_modules/vant/es/field/Field.mjs`)：
- 第 18 行：`rules: Array` 已声明为 prop
- 第 54 行：渲染函数使用 `_createVNode(Cell, _mergeProps({ ...props }, attrs), null)`
- **问题**：如果 `rules` 因任何原因未被识别为已声明 prop，就会进入 `attrs` 并透传到 Cell 组件

## 修复方案

### 1. DataReport.vue - 移除 :rules 数组属性

**修改前**：
```vue
<van-field
  v-model="form.play_count"
  :rules="[{ required: true, message: '请输入播放量' }]"
/>
```

**修改后**：
```vue
<van-field
  v-model="form.play_count"
  required
/>
```

### 2. 添加手动验证逻辑

在 `handleSubmit` 函数中：
```typescript
const handleSubmit = async () => {
  if (!task.value) return
  if (!form.value.play_count || !form.value.comment_count || !form.value.message_count) {
    showToast('请填写所有数据')
    return
  }
  // ... 继续提交逻辑
}
```

### 3. 清理调试代码

移除 `main.ts` 中的临时调试补丁：
- 移除 `Element.prototype.setAttribute` monkey-patch
- 移除 `app.config.errorHandler` 调试代码

## 涉及文件

- `frontend/src/views/DataReport.vue` - 移除 3 个 `:rules` 属性，添加手动验证
- `frontend/src/main.ts` - 清理调试代码

## 经验教训

### 避免数组属性泄漏的最佳实践

1. **优先使用布尔属性**：对于简单的必填验证，使用 `required` 而非 `:rules="[...]"`
2. **显式声明 prop**：自定义组件中明确声明所有 prop，避免 `$attrs` 泄漏
3. **使用 `inheritAttrs: false`**：如果组件不需要透传 attrs，显式设置为 `false`
4. **变量引用优于内联数组**：如果必须使用 `:rules`，使用计算属性或变量引用而非内联数组字面量

### 调试技巧

当遇到类似错误时：
1. 检查是否有数组/对象被当作 prop 传递
2. 查看 Vant 组件源码是否设置了 `inheritAttrs: false`
3. 使用 monkey-patch `Element.prototype.setAttribute` 捕获非法属性名
4. 检查 auto-import 配置是否正确识别组件 prop

## 验证结果

- ✅ 开发服务器正常运行 (http://localhost:5173/)
- ✅ TypeScript 诊断无错误
- ✅ 页面可正常访问，无控制台错误
- ✅ 表单验证功能正常（手动验证）

## 相关技术栈

- Vue 3 + TypeScript
- Vant 4.9.24
- unplugin-vue-components (VantResolver)
