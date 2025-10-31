<template>
  <div class="video-stream-container">
    <div class="video-wrapper">
    <h2 class="stream-title">实时视频流</h2>
    <div id="video-container" class="video-wrapper">
      <video
        muted
        ref="videoRef"
        id="remoteVideo"
        class="video-js"
      ></video>

      <!-- 加载状态提示 -->
      <div class="loading" v-if="isConnecting && !isPlaying">
        <div class="spinner"></div>
        <p>连接中... 请等待摄像头启动</p>
      </div>

      <!-- 错误提示 -->
      <div class="error-message" v-if="errorMessage">
        ⚠️ {{ errorMessage }}
      </div>
    </div>
    </div>
    <!-- 控制按钮 -->
    <div class="controls">
      <button :disabled="!isConnected" @click="AiToAnalyze" class="download-btn">实时场景分析</button>
      <button
        @click="openAnalysis"
        :disabled="!analysisResult"
        class="btn-view-analysis"
      >
        分析报告查询
      </button>
    </div>
    <div class="example-basic">
      <h2 class="stream-title">定时</h2>
      <el-time-picker format="HH:mm" v-model="setTimeValue" @change="setTime" placeholder="Arbitrary time" />
      <div>
        <el-table :data="setTimeData" style="width: 100%" max-height="250">
          <el-table-column fixed prop="time" label="已设时间" width="150" />
          <el-table-column fixed="right" label="操作" min-width="120">
            <template #default="scope">
              <el-button
                link
                type="primary"
                size="small"
                @click.prevent="deleteRow(scope.$index,scope)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

  </div>
</template>

<script setup>
import {ref, onUnmounted, nextTick, onMounted} from 'vue';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
// 引入 HLS 支持插件
import '@videojs/http-streaming';
import router from "@/router/index.js";
import {partdata} from '@/data/data.js';
import { ElLoading } from 'element-plus'
import {global} from "@/main.js";
import { ElMessage } from 'element-plus'
import axios from 'axios'

const deleteRow = async (index,s) => {
  console.log('删除')
  console.log(s.row.workId)
  const res=await fetch(global.$config.serverUrl+'deltime?workid='+s.row.workId,{
    method: 'GET',
  })
  setTimeData.value.splice(index, 1)

  console.log(await res.json())
}
const setTimeValue = ref()
let setTimeData = ref([])
const findTime = async () => {
  const res=await fetch(global.$config.serverUrl+'findtime',{
    method: 'GET',
  })
  const setTimesList=(await res.json()).data
  console.log(setTimesList)
  setTimeData.value=Object.keys(setTimesList).map(key=>{
    console.log(setTimesList[key])
    return {'workId':key,'time':setTimesList[key]}
  })

  console.log(setTimeData.value)
}
const setTime = async () => {
  let HH=''
  let mm=''
  console.log(setTimeValue.value)
  if (!setTimeValue.value) {
    return;
  }
  HH=setTimeValue.value.getHours()
  mm=setTimeValue.value.getMinutes()
  console.log(HH)
  console.log(mm)
  const nowTime=Date.now()
  const res=await fetch(global.$config.serverUrl+"settime?HH="+HH+"&mm="+mm+"&workid="+nowTime,{
    method: 'GET',
  })
  setTimeData.value.push({"workId":nowTime,"time":HH+":"+mm})
  console.log(await res.json())
}

// 获取视频ref元素
let videoRef = ref(null);
// 创造canvas图版
const screenshotCanvas = ref(document.createElement('canvas'));
// 状态管理
const isConnected = ref(false);//是否连接
const isConnecting = ref(false);//是否正在连接
const isPlaying = ref(false);//是否播放
const errorMessage = ref('');//错误信息
const screenshotCaptured = ref(false); // 截图是否已捕获
let analysisResult= ref(false); // 有无分析结果
const screenshotUrl = ref(''); // 截图的URL
let player = null;//视频流播放内置框架
// 视频流地址
let linkUrl = ref('');
// 数据传输
let part2_summary=ref()
let part3_details=ref()
let part4_advice=ref()

// 打开报告
const openAnalysis = async () => {
  partdata.sendpart2_summary=part2_summary.value
  partdata.sendpart3_details=part3_details.value
  partdata.sendpart4_advice=part4_advice.value
  await nextTick()
  router.push("/analysis")
}
// 连接视频流
const connect = async () => {
  // 重置状态
  errorMessage.value = '';
  isConnecting.value = true;
  isPlaying.value = false;
  screenshotCaptured.value = false;
  linkUrl.value = '';
  analysisResult.value = false;
  sessionStorage.removeItem("part2_summary")
  sessionStorage.removeItem("part3_details")
  sessionStorage.removeItem("part4_advice")

  const srcUrl=ref()
  try {
    srcUrl.value=(await axios.post(global.$config.serverUrl+'getUrl')).data.data.url
  }catch(error){
    errorMessage.value="视频流获取失败";
    console.error(error);
    throw error
  }
  try {
    // 设置内部流框架
    player = videojs(videoRef.value, {
      autoplay: true,
      controls: true,
      responsive: true,
      fluid: true,
      sources: [
        {
          src: srcUrl.value, // HLS 流地址
          type: 'application/x-mpegURL' // HLS 协议类型
        }
      ]
    });
    player.play()
    // 连接后
    player.on("canplaythrough",()=>{
      isPlaying.value = true;
      isConnected.value = true;
      isConnecting.value = false;
    })
  } catch (err) {
    errorMessage.value = `连接失败: ${err.message}`;
    console.error(err)
    resetState();
  }
};
// 发送流截图
async function sendImg(base64Image) {
  try {
    // 1. 构造请求参数
    const response = await fetch(global.$config.serverUrl+'save-screenshot', {
      method: 'POST', // 必须与后端接口方法一致（POST）
      headers: {
        'Content-Type': 'application/json', // 告诉后端数据格式为JSON
      },
      body: JSON.stringify({
        image_base64: base64Image, // 截图的base64字符串（前端生成的截图数据）
        filename: `screenshot.png` // 可选：自定义文件名
      })
    });

    // 2. 处理响应状态
    if (!response.ok) {
      // 若HTTP状态码不是200-299，视为错误（如404、500）
      throw new Error(`请求失败：${response.status} ${response.statusText}`);
    }
    // 3. 解析JSON响应（后端返回的JSON数据）
    const result = await response.json();
    return result;
  } catch (error) {
    // 4. 捕获所有错误（网络错误、解析错误、状态码错误等）
    alert('保存失败，请重试');
    console.error(error);
    throw error; // 可选：向上层抛出错误，便于进一步处理
  }
}
// AI去分析
const AiToAnalyze  = async () => {
  // loading
  const loading = ElLoading.service({
    lock: true,
    text: 'Loading',
    background: 'rgba(0, 0, 0, 0.7)',
  })
  try {
    await captureScreenshot()
    const response=await fetch(global.$config.serverUrl+'aitoanalyze',{
      method: 'GET',
    })
    const answers=await response.json()
    console.log(answers)
    if(answers.data.part2_summary==''||answers.data.part3_details==''||answers.data.part4_advice==''){
      ElMessage({
        message: '无风险隐患',
        type: 'success'
      })
    }else {
      part2_summary.value = answers.data.part2_summary;
      part3_details.value = answers.data.part3_details;
      part4_advice.value = answers.data.part4_advice;
      // 分析成功
      analysisResult.value = true;
      ElMessage({
        message: '分析成功请查看',
        type: 'success'
      })
    }
  }catch(err){
    ElMessage.error('截图模糊请重新截图分析!!!')
    console.error(err)
    throw err
  }finally {
    loading.close()
  }
}
// 截图分析功能
const captureScreenshot = async () => {
  if (!isConnected.value || !videoRef.value) return;

  try {
    const video = player.el().querySelector('video');
    const canvas = screenshotCanvas.value;
    // 设置Canvas尺寸与视频一致
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    // 绘制当前视频帧到Canvas
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // 将Canvas内容转为可显示的URL
    const dataUrl = canvas.toDataURL('image/png');
    screenshotUrl.value = dataUrl;
    await sendImg(dataUrl)

    // 更新状态并显示弹窗
    screenshotCaptured.value = true;

  } catch (err) {
    console.error('截图失败:', err);
    errorMessage.value = `截图失败: ${err.message}`;
    throw err
  }
};

// 重置状态
const resetState = () => {
  isConnected.value = false;
  isConnecting.value = false;
  isPlaying.value = false;
  errorMessage.value = '';
  screenshotCaptured.value = false;
  linkUrl.value = '';
  analysisResult.value = false;
};
onMounted(()=>{
  console.log(global.$config.serverUrl)
  findTime()
  if (videoRef.value) {
    connect()
  }
})
// 组件卸载时清理
onUnmounted(() => {
  resetState()
  if (player) {
    player.dispose();
  }
});
</script>
<style>
.example-basic .el-date-editor {
  margin: 8px;
}
</style>
<style>
.demo-tabs > .el-tabs__content {
  padding: 32px;
  color: #6b778c;
  font-size: 32px;
  font-weight: 600;
}
.demo-tabs .custom-tabs-label .el-icon {
  vertical-align: middle;
}
.demo-tabs .custom-tabs-label span {
  vertical-align: middle;
  margin-left: 4px;
}
</style>

<style scoped>


:deep(.video-js){
  height: 563px;
}
:deep(.vjs-loading-spinner) {
  display: none !important; /* 隐藏加载转圈动画 */
}
:deep(.vjs-big-play-button) {
  display: none !important; /* 彻底隐藏大播放按钮（防止类名残留） */
}

/* 可选：隐藏控制栏中的缓冲提示 */
:deep(.vjs-buffer-bar) {
  display: none !important;
}
.video-stream-container {
  display: flex;
  width: fit-content;
  //background-color: #36d399;
  margin: 2vh auto;
  //padding: 20px;
  font-family: Arial, sans-serif;
  .stream-title{
    font-size: 1.5vh;
    background-color: #4d6bfc;
    text-align: center;
    line-height: 3vh;
    height: 3vh;
    width: fit-content;
    padding: 0 1vw;
    padding-top: 0.1vh;
    color: white;
    border-radius: 1vw;
    margin-bottom: 1vh;
  }
}

.video-wrapper {
  position: relative;
  width: 50vw;
  //background: #000;
  border-radius: .8vw;
  overflow: hidden;
}

.loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 4px solid #fff;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 15px;
  background: #ff4444;
  color: white;
  text-align: center;
  z-index: 10;
}

.controls {
  display: flex;
  //background-color: #4CAF50;
  flex-direction: column;
  justify-content: end;
  gap: 1vh;
  align-items: center;
  flex-wrap: wrap;
  margin-left: 1vw;
}

button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-connect {
  background: #4CAF50;
  color: white;
}

.btn-disconnect {
  background: #f44336;
  color: white;
}

.btn-screenshot {
  background: #2196F3;
  color: white;
}

.btn-view-analysis {
  background-color:white ;
  color: #4d6bfc;
  height: 3.5vh;
  line-height: 3.5vh;
  border: .2vh solid #4d6bfc;
  padding: 0vh 1vw;
  border-radius: .3vh;
  text-decoration: none;
  font-size: 1.5vh;
  cursor: pointer;
}
.btn-view-analysis:hover{
  color: white;
  background-color: #4d6bfc;
}
.status {
  margin-left: auto;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 14px;
}

/* 分析结果区域 */
.analysis-result {
  margin-top: 15px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.analysis-result h3 {
  margin-top: 0;
  color: #333;
  font-size: 16px;
}

.analysis-result textarea {
  width: 100%;
  font-size: 14px;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
  resize: none;
  min-height: 120px;
}

/* 截图弹窗样式 */
.screenshot-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}
.close-ctn{
  background: #f44336;
  color: white;
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.close-btn {
  background: #f44336;
  color: white;
  border: none;
  width: 70px;
  height: 40px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.modal-body {
  padding: 20px;
  text-align: center;
}

.screenshot-img {
  max-width: 100%;
  max-height: 500px;
  border-radius: 4px;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.download-btn {
  background-color: #4d6bfc;
  color: white;
  height: 3.5vh;
  line-height: 3.5vh;
  padding: 0vh 1vw;
  border-radius: .3vh;
  text-decoration: none;
  font-size: 1.5vh;
  cursor: pointer;
}

</style>
