# AI医疗导诊与报告解读系统

## 项目简介

基于大语言模型（LLM）的智能医疗服务系统，提供三大核心功能：

- **智能问诊对话**：多轮对话采集患者症状、病史等关键信息
- **科室推荐**：基于症状关键词匹配，推荐最合适的就诊科室（支持12个科室）
- **医疗报告解读**：上传检查报告，AI自动分析指标并生成通俗解读

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Vite |
| 后端 | Python Flask + SQLAlchemy |
| 数据库 | SQLite（可切换MySQL） |
| AI | DeepSeek API（OpenAI兼容）/ Mock模式 |
| OCR | Mock模式（可接入PaddleOCR / 百度OCR） |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- npm 9+

### 1. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（含12个科室种子数据）
python init_db.py

# 启动服务
python app.py
```

后端运行在 `http://localhost:5000`

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 `http://localhost:5173`

### 3. 使用系统

1. 打开浏览器访问 `http://localhost:5173`
2. 注册账号并登录
3. 进入「智能问诊」描述症状，AI助手多轮对话采集信息
4. 进入「科室推荐」查看推荐的就诊科室
5. 进入「报告解读」上传医疗报告，获取AI解读
6. 进入「健康档案」查看历史记录

## 配置LLM API（可选）

默认使用Mock模式演示。如需接入真实LLM，设置环境变量：

```bash
# Windows PowerShell
$env:LLM_API_KEY="your-deepseek-api-key"
$env:LLM_BASE_URL="https://api.deepseek.com/v1"
$env:LLM_MODEL="deepseek-chat"

# Linux/Mac
export LLM_API_KEY="your-deepseek-api-key"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"
```

支持任意OpenAI兼容接口（DeepSeek、通义千问、GLM等）。

## 项目结构

```
ai-medical-system/
├── backend/
│   ├── app.py              # Flask入口
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据库模型
│   ├── init_db.py          # 初始化脚本
│   ├── requirements.txt    # Python依赖
│   ├── services/
│   │   ├── llm_service.py  # LLM服务（Mock + 真实API）
│   │   ├── ocr_service.py  # OCR服务（Mock + PaddleOCR/百度OCR）
│   │   └── dept_service.py # 科室推荐引擎
│   └── routes/
│       ├── auth.py         # 用户认证
│       ├── consultation.py # 智能问诊
│       ├── recommendation.py # 科室推荐
│       ├── report.py       # 报告解读
│       └── records.py      # 健康档案
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── api/            # API封装
│   │   ├── router/         # 路由配置
│   │   └── styles/         # 样式
│   └── package.json
└── README.md
```

## 医疗免责声明

本系统提供的导诊建议和报告解读仅供参考，不能替代专业医生的诊断和治疗方案。如有身体不适，请及时就医。急重症请立即前往医院急诊科。
