# GeoRef Studio V1.0 开发计划

## 1. 目标与交付策略

GeoRef Studio V1.0 的核心目标是打通从普通地图图片到可用 GIS 成果的主流程：

```text
上传图片 -> 创建工程 -> 建立控制点 -> Affine 配准 -> 精度评估 -> 叠加预览 -> 导出 GeoTIFF
```

从项目成功率和开发风险控制考虑，V1.0 按两个交付层级推进：

- V1.0 核心版：优先交付 GeoTIFF 主链路，确保配准工具的核心价值闭环。
- V1.0 完整版：在核心版稳定后补齐 XYZ 瓦片、MBTiles 和成果包管理。

V1.0 不实现用户系统、自动配准、AI 控制点推荐、TPS/多项式变换、WMTS 服务发布等能力。

## 2. 技术架构

### 2.1 前端

- 框架：Vue 3
- 语言：TypeScript
- UI 组件：Element Plus
- 地图组件：Mapbox GL JS
- 状态管理：Pinia
- 网络请求：Axios
- 图片交互：Canvas 或 OpenLayers Image Layer，根据实现复杂度选择

说明：

- V1.0 建议主地图统一使用 Mapbox GL JS，降低双地图引擎维护成本。
- OpenLayers 可作为后续增强项，除非图片窗口或栅格叠加需求证明 Mapbox 实现成本过高。

### 2.2 后端

- 框架：FastAPI
- 语言：Python 3.12
- GIS 处理：GDAL、Rasterio、PyProj
- 数值计算：NumPy
- 图像处理：OpenCV
- 数据库：PostgreSQL + PostGIS
- 缓存/任务状态：Redis
- 文件存储：开发环境本地存储，生产环境预留 MinIO 适配

### 2.3 推荐目录结构

```text
GeoRef_Studio/
  frontend/
    src/
      api/
      components/
      views/
      stores/
      router/
      types/
  backend/
    app/
      api/
      core/
      models/
      schemas/
      services/
      gis/
      workers/
    tests/
  docs/
  storage/
    uploads/
    outputs/
```

## 3. 里程碑计划

### 阶段 0：项目初始化

目标：建立可运行的前后端工程骨架。

任务：

- 初始化 Vue 3 + TypeScript + Element Plus + Pinia + Axios。
- 初始化 FastAPI + SQLAlchemy/Alembic + PostgreSQL 连接。
- 建立开发环境配置文件与本地文件存储目录。
- 建立基础错误码、统一响应结构和日志格式。
- 编写 Docker Compose，包含 PostgreSQL、PostGIS、Redis。

交付物：

- 前端可启动并访问基础页面。
- 后端可启动并提供健康检查接口。
- 数据库迁移可执行。

验收标准：

- `GET /api/health` 返回正常。
- 前后端本地开发环境一条命令可启动。

### 阶段 1：图片管理与工程管理

目标：完成图片上传、图片元数据读取、工程创建和工程状态管理。

任务：

- 实现图片上传接口，支持 PNG、JPG、JPEG、TIFF、BMP。
- 限制单文件大小不超过 500MB。
- 读取图片名称、尺寸、大小、格式、上传时间。
- 实现工程创建、工程列表、工程详情、工程状态更新。
- 前端实现图片上传页、工程列表页、工程创建入口。

接口：

```http
POST /api/image/upload
POST /api/project/create
GET /api/project/list
GET /api/project/{project_id}
```

验收标准：

- 用户可以上传图片并看到图片元信息。
- 用户可以基于图片创建工程。
- 工程初始状态为 `未配准`。

### 阶段 2：配准工作台基础交互

目标：完成双窗口配准工作台的基础布局和交互。

任务：

- 实现顶部工具栏。
- 实现工程信息面板。
- 实现图片窗口，支持缩放、平移、全图显示、鼠标像素坐标显示。
- 实现地图窗口，支持 Mapbox 底图、卫星图/矢量图切换、经纬度显示。
- 实现控制点面板、图层管理面板和精度面板的基础 UI。
- 建立工作台 Pinia 状态，包括当前工程、图片状态、地图状态、控制点集合。

验收标准：

- 用户进入工程后可看到图片和地图两个窗口。
- 鼠标在图片窗口移动时显示 PixelX/PixelY。
- 鼠标在地图窗口移动时显示 Longitude/Latitude。
- 图片窗口缩放和平移流畅可用。

### 阶段 3：控制点管理

目标：完成控制点创建、编辑、删除、启用/禁用。

任务：

- 实现点击图片获取 PixelX/PixelY。
- 实现点击地图获取 Longitude/Latitude。
- 建立“图片点 + 地图点”配对流程，自动生成控制点。
- 实现控制点列表展示。
- 实现控制点删除、编辑、启用、禁用。
- 控制点编号在前端稳定显示，后端以 UUID 存储。

接口：

```http
POST /api/control-point/create
GET /api/control-point/list?project_id={project_id}
PUT /api/control-point/{control_point_id}
DELETE /api/control-point/{control_point_id}
```

验收标准：

- 用户可以通过两次点击生成一个控制点。
- 控制点列表包含编号、PixelX、PixelY、Longitude、Latitude、Residual、Status。
- 禁用的控制点不参与后续配准计算。

### 阶段 4：Affine 配准与精度评估

目标：完成 V1.0 核心配准算法和 RMS 评估。

任务：

- 使用启用状态的控制点计算 Affine 变换矩阵。
- 校验控制点数量，少于 3 个时拒绝执行配准。
- 计算每个控制点的 ΔX、ΔY、Residual。
- 计算综合 RMS。
- 保存配准结果和误差信息。
- 前端展示控制点误差、RMS、误差排序。

接口：

```http
POST /api/georef/run
GET /api/georef/rms?project_id={project_id}
```

核心计算说明：

- 输入：像素坐标 `(pixel_x, pixel_y)` 和地理坐标 `(longitude, latitude)`。
- 输出：Affine 变换参数。
- 坐标系：V1.0 默认 WGS84 / EPSG:4326，后续扩展工程级 CRS 配置。

验收标准：

- 3 个及以上启用控制点可执行配准。
- 配准后每个控制点都有残差。
- 精度面板可显示 RMS 和误差排序。
- 工程状态更新为 `已配准`。

### 阶段 5：配准预览

目标：将配准后的图片叠加到地图底图上进行视觉检查。

任务：

- 根据 Affine 结果计算图片四角地理范围或栅格定位信息。
- 在 Mapbox 中叠加配准图片预览层。
- 支持透明度调整。
- 支持显示/隐藏。
- 支持前后对比。

验收标准：

- 配准结果可在地图窗口叠加预览。
- 透明度调整实时生效。
- 用户可以快速判断控制点质量和配准偏差。

### 阶段 6：GeoTIFF 导出

目标：输出包含空间参考和地理变换信息的 GeoTIFF。

任务：

- 基于原始图片、Affine 变换矩阵和 CRS 生成 GeoTIFF。
- 写入坐标系、地理变换矩阵、空间参考信息。
- 保存导出文件记录。
- 前端提供导出按钮、导出进度和下载入口。

接口：

```http
POST /api/export/geotiff
GET /api/export/list?project_id={project_id}
GET /api/export/download/{export_id}
```

验收标准：

- 用户可以导出 GeoTIFF。
- GeoTIFF 可被 QGIS 或 ArcGIS 正确识别空间参考。
- 导出成功后工程状态更新为 `已导出`。

### 阶段 7：瓦片与 MBTiles 后处理

目标：在 GeoTIFF 主链路稳定后补充瓦片成果。

任务：

- 基于 GeoTIFF 生成 XYZ 瓦片。
- 支持默认 256 x 256 瓦片。
- 支持 XYZ ZIP 下载。
- 支持生成 MBTiles。
- 保存瓦片成果记录。

接口：

```http
POST /api/export/xyz
POST /api/export/mbtiles
```

验收标准：

- 用户可以从已导出的 GeoTIFF 生成 XYZ ZIP。
- 用户可以生成并下载 MBTiles。
- 成果管理中可区分 GeoTIFF、XYZ ZIP、MBTiles。

## 4. 数据库设计

### 4.1 project

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 主键 |
| name | varchar | 工程名称 |
| description | text | 工程描述 |
| image_id | uuid | 关联图片 |
| image_path | varchar | 图片存储路径，冗余便于处理 |
| status | varchar | 未配准、已配准、已导出 |
| create_time | timestamp | 创建时间 |
| update_time | timestamp | 更新时间 |

### 4.2 image_file

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 主键 |
| original_name | varchar | 原始文件名 |
| storage_path | varchar | 存储路径 |
| width | integer | 图片宽度 |
| height | integer | 图片高度 |
| size_bytes | bigint | 文件大小 |
| format | varchar | 文件格式 |
| upload_time | timestamp | 上传时间 |

### 4.3 control_point

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 主键 |
| project_id | uuid | 工程 ID |
| pixel_x | double precision | 图片像素 X |
| pixel_y | double precision | 图片像素 Y |
| longitude | double precision | 经度 |
| latitude | double precision | 纬度 |
| residual | double precision | 综合残差 |
| delta_x | double precision | X 方向误差 |
| delta_y | double precision | Y 方向误差 |
| enabled | boolean | 是否启用 |
| create_time | timestamp | 创建时间 |
| update_time | timestamp | 更新时间 |

### 4.4 georef_result

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 主键 |
| project_id | uuid | 工程 ID |
| transform_type | varchar | V1.0 固定为 affine |
| transform_matrix | jsonb | 变换矩阵 |
| crs | varchar | 默认 EPSG:4326 |
| rms | double precision | 综合 RMS |
| create_time | timestamp | 创建时间 |

### 4.5 export_file

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 主键 |
| project_id | uuid | 工程 ID |
| type | varchar | geotiff、xyz_zip、mbtiles |
| file_path | varchar | 成果文件路径 |
| file_size | bigint | 文件大小 |
| status | varchar | processing、success、failed |
| message | text | 错误或状态说明 |
| create_time | timestamp | 创建时间 |

## 5. API 设计原则

统一响应格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误响应示例：

```json
{
  "code": 40001,
  "message": "At least 3 enabled control points are required",
  "data": null
}
```

建议错误码：

| 错误码 | 含义 |
| --- | --- |
| 40001 | 参数错误 |
| 40002 | 文件格式不支持 |
| 40003 | 文件超过大小限制 |
| 40004 | 控制点数量不足 |
| 40401 | 工程不存在 |
| 50001 | GIS 处理失败 |
| 50002 | 导出失败 |

## 6. 前端页面规划

### 6.1 页面清单

- 工程列表页
- 图片上传页
- 工程创建页
- 配准工作台页
- 成果管理页

### 6.2 配准工作台组件

```text
WorkbenchView
  TopToolbar
  ProjectInfoPanel
  ImageViewer
  MapViewer
  ControlPointPanel
  LayerPanel
  AccuracyPanel
```

### 6.3 工作台关键状态

```ts
type WorkbenchState = {
  projectId: string
  image: ImageFile | null
  controlPoints: ControlPoint[]
  activeStep: 'pick-image' | 'pick-map'
  pendingImagePoint: { pixelX: number; pixelY: number } | null
  georefResult: GeorefResult | null
  previewOpacity: number
  previewVisible: boolean
}
```

## 7. 后端服务规划

### 7.1 服务划分

- ImageService：图片上传、格式校验、元数据读取。
- ProjectService：工程创建、查询、状态流转。
- ControlPointService：控制点增删改查。
- GeorefService：Affine 计算、残差和 RMS 计算。
- PreviewService：预览图层数据准备。
- ExportService：GeoTIFF、XYZ、MBTiles 导出。
- StorageService：本地存储与 MinIO 适配。

### 7.2 GIS 处理边界

GIS 处理逻辑应集中在 `backend/app/gis/`，避免散落在 API 层：

```text
gis/
  affine.py
  residual.py
  geotiff.py
  tiles.py
  crs.py
```

## 8. 测试计划

### 8.1 单元测试

- Affine 矩阵计算。
- 控制点数量校验。
- RMS 计算。
- 图片格式和大小校验。
- GeoTIFF 写入参数校验。

### 8.2 集成测试

- 上传图片 -> 创建工程。
- 新增控制点 -> 执行配准 -> 获取 RMS。
- 执行 GeoTIFF 导出 -> 下载成果。

### 8.3 人工验收

- 使用一张已知范围的测试地图进行配准。
- 在 QGIS 中打开导出的 GeoTIFF，检查定位是否正确。
- 在 Mapbox 预览中检查透明度、显隐、偏差表现。

## 9. 开发优先级

### P0：必须完成

- 图片上传。
- 工程管理。
- 控制点管理。
- Affine 配准。
- RMS 评估。
- 配准预览。
- GeoTIFF 导出。

### P1：建议完成

- XYZ 瓦片导出。
- MBTiles 导出。
- 成果管理列表。
- 导出任务状态。

### P2：暂缓

- 用户系统。
- 自动配准。
- AI 控制点推荐。
- 多种配准算法。
- 在线瓦片服务发布。

## 10. 主要风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| 浏览器加载超大图片卡顿 | 工作台不可用 | 前端使用分块/降采样预览，后端保留原图用于导出 |
| 坐标系处理不严谨 | GeoTIFF 无法正确定位 | V1.0 固定 EPSG:4326，后续再开放 CRS |
| 控制点质量差 | 配准误差大 | 提供 RMS、单点残差和误差排序 |
| GDAL 环境复杂 | 部署失败 | 使用 Docker 固化运行环境 |
| 瓦片生成耗时长 | 请求超时 | 导出任务异步化，前端轮询任务状态 |
| Mapbox 图片叠加精度有限 | 预览与导出不一致 | 预览只用于人工检查，以 GeoTIFF 导出结果为准 |

## 11. 建议开发排期

以 1 名前端、1 名后端、1 名 GIS/全栈开发为参考：

| 周期 | 内容 |
| --- | --- |
| 第 1 周 | 项目初始化、数据库迁移、上传与工程管理 |
| 第 2 周 | 工作台布局、图片窗口、地图窗口 |
| 第 3 周 | 控制点管理、前后端联调 |
| 第 4 周 | Affine 配准、RMS 评估 |
| 第 5 周 | 配准预览、GeoTIFF 导出 |
| 第 6 周 | 测试修复、QGIS 验证、核心版交付 |
| 第 7 周 | XYZ 瓦片导出 |
| 第 8 周 | MBTiles 导出、成果管理、完整 V1.0 交付 |

## 12. V1.0 验收清单

- 可以上传 PNG、JPG、JPEG、TIFF、BMP 图片。
- 可以创建工程并查看工程状态。
- 可以在图片窗口选择像素点。
- 可以在地图窗口选择经纬度点。
- 可以新增、编辑、删除、启用、禁用控制点。
- 少于 3 个启用控制点时不能执行配准。
- 3 个及以上启用控制点时可以执行 Affine 配准。
- 可以显示单点残差和 RMS。
- 可以将配准图片叠加到底图预览。
- 可以调整预览透明度和显隐。
- 可以导出 GeoTIFF。
- GeoTIFF 可在 QGIS 中正确打开并定位。
- 完整版可以导出 XYZ ZIP。
- 完整版可以导出 MBTiles。

## 13. 后续 V2.0 扩展方向

- Projective 变换。
- TPS 变换。
- 多项式配准。
- 自动控制点推荐。
- OSM 自动匹配。
- AI 辅助配准。
- 多坐标系支持。
- 在线瓦片服务。
- WMTS/XYZ 服务发布。
