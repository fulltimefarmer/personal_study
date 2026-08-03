
# 第 27 题：平均工资 - 部门 vs 公司

## 题目描述

有一张 `Employee` 表：

| 列名         | 类型    | 说明           |
|--------------|---------|----------------|
| id           | INT     | 主键           |
| department   | VARCHAR | 部门名称       |
| salary       | DECIMAL | 工资           |

请编写 SQL，对每个部门的每一位员工，计算：
- 该员工在该部门的**薪水排名**（从高到低）
- 该部门薪水的**平均值**
- 该公司所有薪水的**平均值**
- 该员工薪资相较于部门平均薪资是**高于**、**低于**还是**等于**（用 case when）
- 该员工薪资相较于公司平均薪资是**高于**、**低于**还是**等于**

### 示例

**输入：**

| id | department | salary |
|----|------------|--------|
| 1  | 技术部     | 15000  |
| 2  | 技术部     | 12000  |
| 3  | 技术部     | 18000  |
| 4  | 销售部     | 10000  |
| 5  | 销售部     | 13000  |
| 6  | 行政部     | 9000   |

**输出：**

| id | department | salary | dept_rank | dept_avg | company_avg | vs_dept   | vs_company |
|----|------------|--------|-----------|----------|-------------|-----------|------------|
| 1  | 技术部     | 15000  | 2         | 15000    | 12833.33    | 等于      | 高于       |
| 2  | 技术部     | 12000  | 3         | 15000    | 12833.33    | 低于      | 低于       |
| 3  | 技术部     | 18000  | 1         | 15000    | 12833.33    | 高于      | 高于       |
| 4  | 销售部     | 10000  | 2         | 11500    | 12833.33    | 低于      | 低于       |
| 5  | 销售部     | 13000  | 1         | 11500    | 12833.33    | 高于      | 高于       |
| 6  | 行政部     | 9000   | 1         | 9000     | 12833.33    | 等于      | 低于       |

## 考察点

- 窗口函数 `RANK()` + `PARTITION BY`
- 窗口函数 `AVG()` 的 `PARTITION BY` 和 `OVER ()`（全局）的区别
- `CASE WHEN` 多条件比较
- 窗口函数与普通聚合函数的配合

## 解题思路

本题的核心是区分**分区窗口函数**和**全局窗口函数**：

```sql
SELECT id, department, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank,
       ROUND(AVG(salary) OVER (PARTITION BY department), 2) AS dept_avg,
       ROUND(AVG(salary) OVER (), 2) AS company_avg,
       CASE
           WHEN salary > AVG(salary) OVER (PARTITION BY department) THEN '高于'
           WHEN salary < AVG(salary) OVER (PARTITION BY department) THEN '低于'
           ELSE '等于'
       END AS vs_dept,
       CASE
           WHEN salary > AVG(salary) OVER () THEN '高于'
           WHEN salary < AVG(salary) OVER () THEN '低于'
           ELSE '等于'
       END AS vs_company
FROM Employee
ORDER BY department, dept_rank;
```

### 窗口函数的三类作用域

| 写法 | 作用域 | 说明 |
|------|--------|------|
| `AVG(salary) OVER (PARTITION BY department)` | 部门内 | 每个部门内单独计算平均工资 |
| `AVG(salary) OVER ()` | 全局 | 在所有行上计算平均工资 |
| `AVG(salary) OVER (ORDER BY ...)` | 累计 | 按顺序累加计算平均值 |

`OVER ()` 不加任何分区和排序条件，表示在整个结果集上计算。
