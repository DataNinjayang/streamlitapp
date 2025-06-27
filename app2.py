import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# -------------------
# 全局配置
# -------------------
# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# -------------------
# 数据加载模块
# -------------------
@st.cache_data
def load_data(file_path=None):
    """加载Excel数据并进行基础处理"""
    # 如果没有提供文件路径，尝试使用默认路径或提示用户上传文件
    if file_path is None:
        file_path = "merged_data.xlsx"  # 与GitHub仓库中的文件名一致
        df = pd.read_excel(file_path)
    
    try:
        # 读取文件
        df = pd.read_excel(file_path)
        # 标准化列名：处理默认索引列
        if "Unnamed: 0" in df.columns:
            df = df.rename(columns={"Unnamed: 0": "股票代码"})
        # 校验关键列
        required_columns = ["股票代码"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"数据中缺少必要列: {', '.join(missing_cols)}")
            return None
        return df
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return None

# -------------------
# 综合图表绘制模块
# -------------------
def plot_overall_interactive_chart(df):
    """绘制全量数据的综合性交互分析图表"""
    st.subheader("人工智能板块上市公司数字化转型综合分析")
    
    # 自动识别行业分类列（支持多语言/多命名方式）
    industry_column = None
    industry_candidates = ['行业', '所属行业', '行业分类', 'industry', 'Industry']
    for col in industry_candidates:
        if col in df.columns:
            industry_column = col
            break
    
    # 提取数值指标列（排除股票代码）
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    if "股票代码" in numeric_columns:
        numeric_columns.remove("股票代码")
    
    # -------------------
    # 1. 行业分布与指数概览看板
    # -------------------
    st.markdown("### 行业分布与数字化转型指数概览")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if industry_column:
            # 计算行业企业数量
            industry_counts = df[industry_column].value_counts().reset_index()
            industry_counts.columns = [industry_column, '企业数量']
            # 绘制饼图
            fig_pie = px.pie(
                industry_counts, 
                values='企业数量', 
                names=industry_column,
                title='各行业企业数量占比',
                template='plotly_white',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("数据中未找到行业分类列，无法绘制行业分布图表")
    
    with col2:
        if numeric_columns:
            # 自动选择默认指标（优先使用总指数）
            default_metric = "数字化转型总指数"
            if default_metric not in numeric_columns:
                default_metric = numeric_columns[0]
            # 绘制直方图
            fig_hist = px.histogram(
                df, 
                x=default_metric, 
                title=f'{default_metric}分布情况',
                nbins=20,
                template='plotly_white',
                color_discrete_sequence=['#00A1FF']
            )
            # 添加平均值和中位数参考线
            fig_hist.add_vline(
                x=df[default_metric].mean(), 
                line_dash="dash", 
                line_color="red",
                annotation_text="平均值",
                annotation_position="top left"
            )
            fig_hist.add_vline(
                x=df[default_metric].median(), 
                line_dash="dash", 
                line_color="green",
                annotation_text="中位数",
                annotation_position="top right"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("数据中未找到数值指标列，无法绘制分布图表")
    
    # -------------------
    # 2. 指标关联交互式分析
    # -------------------
    st.markdown("### 数字化转型指标交互式关联分析")
    if len(numeric_columns) >= 2:
        # 优化指标选择默认值
        x_default = "数字化转型总指数" if "数字化转型总指数" in numeric_columns else numeric_columns[0]
        y_default = "技术应用" if "技术应用" in numeric_columns else (numeric_columns[1] if len(numeric_columns) > 1 else numeric_columns[0])
        
        x_col = st.selectbox(
            "X轴指标", 
            numeric_columns,
            index=numeric_columns.index(x_default)
        )
        y_col = st.selectbox(
            "Y轴指标", 
            numeric_columns,
            index=numeric_columns.index(y_default) if y_default in numeric_columns else 0
        )
        
        # 确定悬浮标签字段
        hover_name = "企业名称" if "企业名称" in df.columns else "股票代码"
        
        # 添加颜色分组选项
        color_options = ["无分组"] + ([industry_column] if industry_column else [])
        color_by = st.selectbox(
            "颜色分组", 
            color_options,
            index=1 if industry_column else 0
        )
        
        # 绘制散点图（支持行业颜色分组）
        fig_scatter = px.scatter(
            df, 
            x=x_col, 
            y=y_col,
            color=color_by if color_by != "无分组" else None,
            hover_name=hover_name,
            title=f'{x_col} 与 {y_col} 关联分析',
            template='plotly_white',
            color_continuous_scale='Viridis'
        )
        
        # 添加趋势线
        if st.checkbox("显示趋势线"):
            fig_scatter.update_traces(
                mode='markers+lines',
                line=dict(color='black', width=2, dash='dash')
            )
        
        fig_scatter.update_layout(
            height=500,
            hovermode='x unified',
            font=dict(size=12)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("数据中数值指标少于2个，无法进行关联分析")
    
    # -------------------
    # 3. 行业指标对比看板
    # -------------------
    st.markdown("### 各行业数字化转型指标对比")
    if industry_column and numeric_columns:
        # 智能筛选关键指标（优先业务相关指标）
        key_metrics = ["数字化转型总指数", "战略转型", "技术应用", "组织变革", "数据价值", "流程优化"]
        available_metrics = [col for col in key_metrics if col in numeric_columns]
        if not available_metrics:
            available_metrics = numeric_columns[:3]  # 至少选择3个指标
        
        # 添加指标选择器
        selected_metrics = st.multiselect(
            "选择要比较的指标",
            available_metrics,
            default=available_metrics
        )
        
        if not selected_metrics:
            st.warning("请至少选择一个指标进行比较")
            return
        
        # 计算行业平均指标
        industry_data = df.groupby(industry_column)[selected_metrics].mean().reset_index()
        
        # 数据格式转换（适用于雷达图）
        industry_data_melt = pd.melt(
            industry_data, 
            id_vars=[industry_column], 
            value_vars=selected_metrics,
            var_name='指标', 
            value_name='平均值'
        )
        
        # 绘制雷达图（行业间指标对比）
        fig_radar = px.line_polar(
            industry_data_melt, 
            r='平均值', 
            theta='指标', 
            color=industry_column,
            line_close=True,
            title='各行业数字化转型指标雷达图对比',
            template='plotly_white',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        
        # 动态设置雷达图范围
        min_val = industry_data_melt['平均值'].min() * 0.9
        max_val = industry_data_melt['平均值'].max() * 1.1
        
        fig_radar.update_layout(
            height=600,
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[min_val, max_val]
                )
            ),
            font=dict(size=11)
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        if not industry_column:
            st.info("数据中未找到行业分类列，无法进行行业对比分析")
        if not numeric_columns:
            st.info("数据中未找到数值指标列，无法进行指标对比分析")
    
    # -------------------
    # 4. 企业排名榜单
    # -------------------
    st.markdown("### 企业数字化转型排名榜单")
    if numeric_columns:
        # 选择排名指标
        ranking_metric = st.selectbox(
            "选择排名指标",
            numeric_columns,
            index=numeric_columns.index("数字化转型总指数") if "数字化转型总指数" in numeric_columns else 0
        )
        
        # 选择排名数量
        top_n = st.slider("显示数量", min_value=5, max_value=50, value=10, step=5)
        
        # 升序或降序
        ascending = st.radio(
            "排序方式",
            ["降序（从高到低）", "升序（从低到高）"],
            index=0
        )
        ascending = ascending == "升序（从低到高）"
        
        # 获取排名数据
        ranking_data = df.sort_values(by=ranking_metric, ascending=ascending).head(top_n)
        
        # 显示排名表格
        if "企业名称" in df.columns:
            display_columns = ["企业名称", "股票代码", ranking_metric]
            display_columns = [col for col in display_columns if col in df.columns]
            st.dataframe(ranking_data[display_columns].reset_index(drop=True), use_container_width=True)
        else:
            st.dataframe(ranking_data[["股票代码", ranking_metric]].reset_index(drop=True), use_container_width=True)
    else:
        st.info("数据中未找到数值指标列，无法生成排名榜单")
    
    return numeric_columns, industry_column  # 返回处理后的列信息

# -------------------
# 页面布局与逻辑
# -------------------
def main():
    """主函数：配置页面并协调各模块运行"""
    # 页面基础设置
    st.set_page_config(
        page_title="数字化转型综合分析系统", 
        layout="wide",
        page_icon="📊"
    )
    
    # 页面标题与简介
    st.title("人工智能板块上市公司数字化转型综合分析系统")
    st.markdown("""
    本系统通过交互式图表展示人工智能板块上市公司数字化转型整体情况，
    下方查询功能支持检索特定企业的详细数据。
    """, unsafe_allow_html=False)
    
    # 添加文件上传功能
    st.sidebar.header("数据设置")
    uploaded_file = st.sidebar.file_uploader("上传Excel文件", type=["xlsx", "xls"])
    
    # 选择使用上传的文件还是默认文件
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    else:
        df = load_data()
    
    if df is not None:
        # 绘制全量数据综合图表并获取数值列和行业列
        numeric_columns, industry_column = plot_overall_interactive_chart(df)
        
        # -------------------
        # 企业数据查询模块
        # -------------------
        st.subheader("企业数字化转型数据查询")
        
        # 数据结构预览
        if st.checkbox("查看数据结构预览"):
            st.dataframe(df.head(5), use_container_width=True)
            st.write(f"数据列: {', '.join(df.columns)}")
        
        # 查询条件布局
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            query_text = st.text_input(
                "请输入股票代码或企业名称", 
                placeholder="例如: 300884 或 科大讯飞",
                help="支持输入股票代码或企业名称进行查询"
            )
        with col2:
            # 动态生成查询依据选项
            query_by_options = ["股票代码"]
            if "企业名称" in df.columns:
                query_by_options.append("企业名称")
            query_by = st.radio(
                "查询依据",
                query_by_options,
                help="选择按股票代码还是企业名称进行查询"
            )
        with col3:
            query_method = st.radio(
                "查询方式",
                ["精确查询", "模糊查询"],
                help="精确查询需输入完整内容，模糊查询可输入部分内容匹配"
            )
        
        # 查询按钮逻辑
        if st.button("查询", type="primary"):
            if not query_text.strip():
                st.warning("请输入查询内容", icon="⚠️")
                return
            
            query_text = query_text.strip()
            matching_data = pd.DataFrame()
            
            try:
                if query_by == "股票代码":
                    # 股票代码查询（支持精确/模糊）
                    if query_method == "精确查询":
                        code_int = int(query_text)
                        matching_data = df[df["股票代码"] == code_int]
                    else:  # 模糊查询
                        matching_data = df[df["股票代码"].astype(str).str.contains(query_text)]
                else:  # 企业名称查询
                    if "企业名称" not in df.columns:
                        st.error("数据中无企业名称列，无法使用企业名称查询", icon="❌")
                        return
                    if query_method == "精确查询":
                        matching_data = df[df["企业名称"] == query_text]
                    else:  # 模糊查询
                        matching_data = df[df["企业名称"].str.contains(query_text, na=False)]
            except ValueError:
                st.error("股票代码需为整数，请输入有效的股票代码", icon="🚨")
                return
            except Exception as e:
                st.error(f"查询过程中发生错误: {str(e)}", icon="🚨")
                return
            
            # 展示查询结果
            if not matching_data.empty:
                st.subheader(f"查询结果：共找到{len(matching_data)}家企业")
                st.dataframe(matching_data, use_container_width=True, height=300)
                
                # 为查询结果添加可视化分析
                if len(matching_data) > 0 and len(numeric_columns) > 0:
                    st.subheader("查询结果指标分析")
                    
                    # 绘制查询结果的指标雷达图
                    if industry_column and len(matching_data) <= 10:  # 限制企业数量，避免雷达图过于复杂
                        company_data = matching_data.copy()
                        company_name_col = "企业名称" if "企业名称" in company_data.columns else "股票代码"
                        
                        # 筛选指标
                        radar_metrics = [col for col in ["数字化转型总指数", "战略转型", "技术应用", "组织变革", "数据价值", "流程优化"] if col in numeric_columns]
                        if not radar_metrics:
                            radar_metrics = numeric_columns[:min(6, len(numeric_columns))]
                        
                        # 准备雷达图数据
                        company_radar_data = pd.melt(
                            company_data,
                            id_vars=[company_name_col],
                            value_vars=radar_metrics,
                            var_name='指标',
                            value_name='值'
                        )
                        
                        # 绘制雷达图
                        fig_company_radar = px.line_polar(
                            company_radar_data,
                            r='值',
                            theta='指标',
                            color=company_name_col,
                            line_close=True,
                            title='查询企业数字化转型指标对比',
                            template='plotly_white',
                            color_discrete_sequence=px.colors.qualitative.Plotly
                        )
                        
                        # 设置雷达图范围
                        fig_company_radar.update_layout(
                            height=500,
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, company_radar_data['值'].max() * 1.1]
                                )
                            )
                        )
                        st.plotly_chart(fig_company_radar, use_container_width=True)
                    
                    # 绘制查询结果的指标对比条形图
                    compare_metrics = st.multiselect(
                        "选择要比较的指标",
                        numeric_columns,
                        default=numeric_columns[:min(3, len(numeric_columns))]
                    )
                    
                    if compare_metrics and len(matching_data) > 0:
                        if "企业名称" in matching_data.columns:
                            compare_data = matching_data.melt(
                                id_vars=["企业名称"],
                                value_vars=compare_metrics,
                                var_name="指标",
                                value_name="值"
                            )
                            fig_bar = px.bar(
                                compare_data,
                                x="企业名称",
                                y="值",
                                color="指标",
                                barmode="group",
                                title="企业指标对比",
                                template="plotly_white"
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else:
                            st.info("数据中缺少企业名称列，无法生成对比图表")
            else:
                st.warning(f"未找到符合条件的企业记录", icon="⚠️")
                st.info("请确认输入内容是否正确，或查看数据结构预览中的代码/名称列表", icon="ℹ️")
    else:
        st.error("数据加载失败，请检查文件路径是否正确或文件格式是否支持", icon="🚨")

# 执行主函数
if __name__ == "__main__":
    main()    