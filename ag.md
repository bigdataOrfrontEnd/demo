# ClientPageTable 数据刷新时保留行选中状态

## 问题

`ClientPageTable` 在数据刷新时内部调用 `setRowData()` 全量替换数据，已勾选的行会被全部清除。

## 前置条件

必须配置 `getRowNodeId`，用于唯一标识每行数据：

```tsx
props: {
  getRowNodeId: (data) => data.id,
  rowSelection: 'multiple',
}
```

## 使用方式

将下面的 `handleTableReady` 传入 `tableConfig.onTableReady` 即可：

```tsx
import React, { useCallback } from 'react';
import { AgGrid } from '@hzbank/quantex-design';

function MyPage() {
  const handleTableReady = useCallback((store) => {
    const gridApi = store.getGridApi();
    const gridOptions = (gridApi as any).gridOptionsWrapper?.gridOptions || {};
    const getRowId = gridOptions.getRowNodeId || ((data) => gridOptions.getRowId?.({ data }));

    if (!getRowId) return;

    const originalReload = store.reload.bind(store);

    store.reload = function () {
      const ids = new Set<string>();
      gridApi.getSelectedNodes().forEach((n) => {
        if (n.data) ids.add(String(getRowId(n.data)));
      });

      originalReload();

      if (ids.size > 0) {
        const restore = () => {
          gridApi.forEachNode((node) => {
            if (node.data && ids.has(String(getRowId(node.data)))) {
              node.setSelected(true, false);
            }
          });
          gridApi.removeEventListener('modelUpdated', restore);
        };
        gridApi.addEventListener('modelUpdated', restore);
      }
    };
  }, []);

  return (
    <AgGrid.ClientPageTable
      tableConfig={{
        tableId: 'my-table',
        onTableReady: handleTableReady,
        props: {
          getRowNodeId: (data) => data.id,
          rowSelection: 'multiple',
          columnDefs: [
            { checkboxSelection: true, headerCheckboxSelection: true, width: 50 },
            { headerName: '名称', field: 'name' },
          ],
        },
      }}
      searchApi={AgGrid.createSearchApi({
        api: 'yourService',
        url: '/api/list',
      })}
    />
  );
}
```

## 原理

```
store.reload() 被调用
  → 包装函数先 getSelectedNodes() 记下勾选行的 ID
  → 调原始 reload() → setRowData(list) → 勾选被清除
  → modelUpdated 事件触发 → 遍历新数据，匹配 ID 的行重新勾选
```

## 注意

- `setSelected(true, false)` 第二个参数 `false` 表示不触发 `selectionChanged` 事件，避免业务侧的选中回调被意外多次触发
- 翻页切换时不保留跨页选中（翻页走 `setTableData`，不走 `reload`）
