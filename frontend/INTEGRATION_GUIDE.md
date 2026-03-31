# 集成 react-diff-viewer 和 recharts 指南

## 1. 安装依赖

```bash
cd frontend
npm install react-diff-viewer recharts
npm install --save-dev @types/react-diff-viewer
```

## 2. react-diff-viewer 集成

### 使用示例

在 `AuditQueue.enhanced.tsx` 中替换简单的 diff 视图：

```tsx
import ReactDiffViewer from 'react-diff-viewer';

// 在组件中使用
<ReactDiffViewer
  oldValue={selectedItem.originalContent || ''}
  newValue={selectedItem.content}
  splitView={true}
  leftTitle="原始内容"
  rightTitle="AI 生成内容"
  useDarkTheme={true}
  styles={{
    variables: {
      dark: {
        diffViewerBackground: '#1f2937',
        color: '#f3f4f6',
        addedBackground: '#064e3b',
        addedColor: '#d1fae5',
        removedBackground: '#7f1d1d',
        removedColor: '#fee2e2',
      }
    }
  }}
/>
```

## 3. recharts 集成

### 使用示例

替换简单的柱状图为专业的图表：

```tsx
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// 在组件中使用
<ResponsiveContainer width="100%" height={200}>
  <BarChart data={trendData}>
    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
    <XAxis dataKey="date" stroke="#9ca3af" />
    <YAxis stroke="#9ca3af" />
    <Tooltip
      contentStyle={{
        backgroundColor: '#1f2937',
        border: '1px solid #374151',
        color: '#f3f4f6'
      }}
    />
    <Legend />
    <Bar dataKey="approved" fill="#10b981" name="通过" />
    <Bar dataKey="rejected" fill="#ef4444" name="驳回" />
    <Bar dataKey="pending" fill="#f59e0b" name="待审核" />
  </BarChart>
</ResponsiveContainer>
```

## 4. 完整的增强组件

创建 `AuditQueue.professional.tsx`，包含：
- react-diff-viewer 专业 diff 视图
- recharts 专业图表
- 更丰富的分析维度
- 审核自动化规则引擎

## 5. 性能优化

### Code Splitting

```tsx
const ReactDiffViewer = lazy(() => import('react-diff-viewer'));
const Recharts = lazy(() => import('recharts'));

// 使用 Suspense
<Suspense fallback={<div>Loading...</div>}>
  <ReactDiffViewer ... />
</Suspense>
```

### Tree Shaking

只导入需要的图表组件：

```tsx
// ✅ 好的做法
import { BarChart, Bar } from 'recharts';

// ❌ 避免
import * as Recharts from 'recharts';
```

## 6. 主题定制

### Dark Theme 配置

```tsx
const darkTheme = {
  colors: {
    diffViewerBackground: '#1f2937',
    diffViewerColor: '#f3f4f6',
    addedBackground: '#064e3b',
    addedColor: '#d1fae5',
    removedBackground: '#7f1d1d',
    removedColor: '#fee2e2',
    wordAddedBackground: '#065f46',
    wordRemovedBackground: '#991b1b',
  }
};
```

## 7. 功能增强

### 审核自动化规则引擎

```typescript
interface AutoAuditRule {
  id: string;
  name: string;
  conditions: {
    field: string;
    operator: 'contains' | 'equals' | 'regex';
    value: string;
  }[];
  action: 'auto_approve' | 'auto_reject' | 'flag_for_review';
  priority: number;
  enabled: boolean;
}

class AutoAuditEngine {
  private rules: AutoAuditRule[] = [];
  
  addRule(rule: AutoAuditRule): void {
    this.rules.push(rule);
    this.rules.sort((a, b) => b.priority - a.priority);
  }
  
  async evaluate(content: AuditItem): Promise<AutoAuditResult> {
    for (const rule of this.rules) {
      if (!rule.enabled) continue;
      
      const matches = await this.evaluateConditions(rule.conditions, content);
      if (matches) {
        return {
          ruleId: rule.id,
          action: rule.action,
          confidence: 0.9
        };
      }
    }
    
    return null;
  }
}
```

## 8. 测试

```tsx
import { render, screen } from '@testing-library/react';
import AuditQueue from './AuditQueue.professional';

describe('AuditQueue Professional', () => {
  it('renders diff viewer correctly', () => {
    render(<AuditQueue />);
    expect(screen.getByText('内容对比')).toBeInTheDocument();
  });
  
  it('renders charts correctly', () => {
    render(<AuditQueue />);
    expect(screen.getByRole('graphics-document')).toBeInTheDocument();
  });
});
```

## 9. 预期效果

### Diff 视图
- 并排显示原始和 AI 生成内容
- 绿色高亮新增内容
- 红色高亮删除内容
- 支持行号和折叠

### 图表
- 审核趋势柱状图
- 情绪分布饼图
- 响应时间折线图
- 平台分布环形图

### 自动化规则
- 基于关键词自动审批
- 基于情绪自动标记
- 基于优先级自动排序
- 自定义规则引擎

## 10. 后续优化

1. 实现实时协作审核
2. 添加 AI 推荐置信度可视化
3. 实现审核工作流自定义
4. 添加批量智能审核
5. 实现审核报表导出
