# 绩点查询与后悔

一个可本地运行、可打包为 exe 的 CSV 绩点查询工具。

- 打开后初始为空面板，提示上传 CSV
- 支持拖拽上传和按钮选择上传
- 上传后显示学期筛选、课程列表、计入切换、绩点计算
- 支持将当前计算结果下载为 CSV

## 1. 功能概览

- 上传 CSV（支持拖拽/手动选择）
- 按学期筛选
- 每门课手动切换是否计入
- 一键恢复初始计入状态
- 计算加权平均绩点（按学分加权）
- 下载当前结果 CSV

## 2. 数据格式要求

### 2.1 必要列（列名必须完全一致）

- 课程名称
- 修读时间
- 学分
- 等第
- 绩点

### 2.2 可选列

- 课程类型
- 备注

可选列可以不存在；如果存在，会在表格中展示。

### 2.3 等第与绩点规则

仅允许以下等第：

- A+, A, A-, B+, B, B-, C+, C, C-, D, D-, F, P, NP

对应绩点规则：

- A+, A: 必须是 4
- A-: 3.7 到 3.8
- B+: 3.3 到 3.6
- B: 3.0 到 3.2
- B-: 2.7 到 2.9
- C+: 2.3 到 2.6
- C: 2.0 到 2.2
- C-: 1.7 到 1.9
- D: 必须是 1.3
- D-: 必须是 1.0
- F, P, NP: 视为不计入绩点（可视作待补考/通过不计入）

### 2.4 其他校验

- 学分必须是大于 0 的数字
- 修读时间不能为空
- 非 F/P/NP 的课程，绩点不能为空

## 3. 快速运行（源码方式）

1. 创建并激活虚拟环境
2. 安装依赖
3. 运行程序

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python web_app.py
```

默认会打开浏览器：

- http://127.0.0.1:8000

也可以双击：

- start_web.bat

## 4. 使用流程

1. 打开软件后先上传 CSV
2. 若格式错误，会显示错误提示
3. 上传成功后显示课程面板
4. 勾选学期范围
5. 在课程表里切换“计入”复选框
6. 点击“计算绩点”刷新结果
7. 如需回到默认计入，点“恢复初始状态”
8. 如需导出，点“下载当前结果CSV”

## 5. 示例文件

- sample_courses.csv

这是脱敏示例文件，可直接上传测试，不包含你的隐私课程信息。

## 6. 打包 exe

### 6.1 一键打包

双击：

- build_exe.bat

打包成功后产物在：

- dist/GPAQueryRegret.exe

### 6.2 手动打包命令

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name GPAQueryRegret --add-data "templates;templates" web_app.py
```

## 7. 发布到 GitHub

```bash
git init
git add .
git commit -m "feat: GPA query and regret app with CSV upload and exe packaging"
# 你的仓库 URL 自行替换
# 例如: https://github.com/<your-name>/<repo>.git
git remote add origin <repo-url>
git branch -M main
git push -u origin main
```

发布建议：

1. 在 GitHub 创建一个新仓库（例如 gpa-query-regret）
2. 首次 push 后，到 GitHub 页面创建 Release
3. 将 dist/GPAQueryRegret.exe 上传到 Release 作为可下载文件

## 8. 颜色说明（等第边框）

- A、A+、P: 红色
- A-: 橙色
- B+: 黄色
- B: 淡绿色
- B-: 深绿色
- C+: 蓝色
- C: 深蓝色
- C-: 紫色
- D: 深紫色
- D-、F、NP: 灰色
