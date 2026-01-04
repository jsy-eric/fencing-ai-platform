// 时间轴标注系统
class TimelineAnnotator {
    constructor() {
        this.moments = [];
        this.timelineContainer = null;
        this.currentVideo = null;
        this.videoDuration = 0;
    }

    init(containerId = 'video-timeline') {
        this.timelineContainer = document.getElementById(containerId);
        if (!this.timelineContainer) {
            this.timelineContainer = document.createElement('div');
            this.timelineContainer.id = containerId;
            this.timelineContainer.className = 'video-timeline';
            const videoContainer = document.getElementById('video-player');
            if (videoContainer && videoContainer.parentNode) {
                videoContainer.parentNode.insertBefore(this.timelineContainer, videoContainer.nextSibling);
            }
        }
    }

    async loadKeyMoments(videoUrl, duration) {
        try {
            // 保存视频时长
            this.videoDuration = duration || 0;
            console.log(`[Timeline] 开始加载关键时刻，视频URL: ${videoUrl}, 时长: ${duration}秒`);
            
            const response = await fetch('/api/detect_key_moments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    duration: duration
                })
            });

            const data = await response.json();
            console.log('[Timeline] API响应:', data);
            
            if (data.success) {
                this.moments = data.moments || [];
                console.log(`[Timeline] 检测到${this.moments.length}个关键时刻:`, this.moments);
                
                if (this.moments.length > 0) {
                    this.renderTimeline();
                } else {
                    console.warn('[Timeline] 关键时刻数组为空');
                    // 即使为空也渲染，显示空状态
                    this.renderTimeline();
                }
            } else {
                console.error('[Timeline] 关键时刻检测失败:', data);
                // 即使失败也尝试渲染空状态
                this.moments = [];
                this.renderTimeline();
            }
        } catch (error) {
            console.error('[Timeline] 加载关键时刻失败:', error);
            // 即使出错也尝试渲染空状态
            this.moments = [];
            this.renderTimeline();
        }
    }

    renderTimeline() {
        console.log('[Timeline] renderTimeline 被调用');
        
        if (!this.timelineContainer) {
            console.log('[Timeline] 时间轴容器不存在，正在初始化...');
            this.init();
        }

        const timelineTitle = window.i18n ? window.i18n.t('timeline.title', '关键时刻') : '关键时刻';
        this.timelineContainer.innerHTML = `<div class="timeline-header">${timelineTitle}</div>`;
        const timelineBar = document.createElement('div');
        timelineBar.className = 'timeline-bar';

        // 获取视频时长
        const videoDuration = this.getVideoDuration();
        console.log(`[Timeline] 渲染时间轴，视频时长: ${videoDuration}秒，关键时刻数: ${this.moments.length}`);
        console.log('[Timeline] 关键时刻详情:', JSON.stringify(this.moments, null, 2));
        
        if (this.moments.length === 0) {
            console.warn('[Timeline] 没有关键时刻可显示');
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'timeline-empty';
            emptyMsg.textContent = '暂无关键时刻';
            timelineBar.appendChild(emptyMsg);
            this.timelineContainer.appendChild(timelineBar);
            // 即使没有关键时刻，也尝试渲染描述区域（显示空状态）
            this.renderMomentDescriptions([]);
            return;
        }
        
        // 创建数据快照，确保时间轴和描述区域使用完全相同的数据
        // 深拷贝并排序，避免后续修改影响
        const sortedMoments = this.moments
            .map(m => ({
                time: m.time,
                type: m.type,
                description: m.description,
                knowledge: m.knowledge ? {
                    title: m.knowledge.title,
                    content: m.knowledge.content,
                    tips: m.knowledge.tips ? [...m.knowledge.tips] : []
                } : null
            }))
            .sort((a, b) => a.time - b.time);
        
        console.log(`[Timeline] 数据快照创建完成，排序后的关键时刻:`, sortedMoments);
        console.log(`[Timeline] 数据快照验证:`, this.validateMomentsData(sortedMoments));
        
        // 使用数据快照渲染时间轴标记
        sortedMoments.forEach((moment, index) => {
            const marker = this.createMarker(moment, videoDuration);
            timelineBar.appendChild(marker);
        });

        this.timelineContainer.appendChild(timelineBar);
        
        // 使用相同的数据快照渲染时间点描述列表
        console.log('[Timeline] 准备渲染时间点描述，使用数据快照，关键时刻数:', sortedMoments.length);
        this.renderMomentDescriptions(sortedMoments);
        
        // 渲染完成后，进行数据一致性验证
        setTimeout(() => {
            this.validateTimelineConsistency(sortedMoments, videoDuration);
        }, 100); // 延迟100ms确保DOM已更新
        
        console.log(`[Timeline] 时间轴渲染完成，共显示${sortedMoments.length}个时间点`);
    }

    renderMomentDescriptions(moments) {
        console.log('[Timeline] renderMomentDescriptions 被调用，moments:', moments);
        console.log('[Timeline] moments类型:', typeof moments, '长度:', moments ? moments.length : 0);
        
        // 数据验证：确保传入的moments是有效的数组
        if (!Array.isArray(moments)) {
            console.error('[Timeline] renderMomentDescriptions 收到无效数据，不是数组:', moments);
            moments = [];
        }
        
        // 验证数据完整性
        const validationResult = this.validateMomentsData(moments);
        if (!validationResult.valid) {
            console.error('[Timeline] 数据验证失败:', validationResult.errors);
            // 即使验证失败，也继续渲染，但使用空数组
            moments = [];
        } else {
            console.log('[Timeline] 数据验证通过:', validationResult);
        }
        
        // 获取或创建描述容器
        let descriptionsContainer = document.getElementById('timeline-descriptions');
        console.log('[Timeline] 描述容器是否存在:', !!descriptionsContainer);
        
        if (!descriptionsContainer) {
            console.log('[Timeline] 描述容器不存在，正在创建...');
            // 如果HTML中没有，创建一个新的
            descriptionsContainer = document.createElement('div');
            descriptionsContainer.id = 'timeline-descriptions';
            descriptionsContainer.className = 'timeline-descriptions';
            
            // 插入到时间轴容器之后
            if (this.timelineContainer && this.timelineContainer.parentNode) {
                console.log('[Timeline] 插入到时间轴容器之后');
                this.timelineContainer.parentNode.insertBefore(
                    descriptionsContainer, 
                    this.timelineContainer.nextSibling
                );
            } else {
                // 如果时间轴容器不存在，插入到video-container
                const videoContainer = document.querySelector('.video-container');
                if (videoContainer) {
                    console.log('[Timeline] 插入到video-container');
                    videoContainer.appendChild(descriptionsContainer);
                } else {
                    console.error('[Timeline] 无法找到合适的容器，描述区域无法显示');
                    return;
                }
            }
        }
        
        // 强制清空现有内容 - 确保每次渲染都从干净的状态开始
        descriptionsContainer.innerHTML = '';
        descriptionsContainer.textContent = ''; // 双重清空，确保没有残留
        console.log('[Timeline] 已强制清空描述容器内容');
        
        if (!moments || moments.length === 0) {
            console.warn('[Timeline] 没有关键时刻，显示空状态');
            // 显示空状态消息
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'timeline-empty';
            emptyMsg.textContent = '暂无时间点描述';
            descriptionsContainer.appendChild(emptyMsg);
            descriptionsContainer.style.display = 'block';
            return;
        }
        
        // 创建标题
        const title = document.createElement('h4');
        title.className = 'timeline-descriptions-title';
        title.textContent = window.i18n ? window.i18n.t('timeline.descriptions_title', '时间点说明') : '时间点说明';
        descriptionsContainer.appendChild(title);
        console.log('[Timeline] 已添加标题');
        
        // 创建描述列表
        const descriptionsList = document.createElement('div');
        descriptionsList.className = 'timeline-descriptions-list';
        
        console.log('[Timeline] 开始创建描述项，数量:', moments.length);
        console.log('[Timeline] 描述项数据详情:', moments.map(m => ({ time: m.time, type: m.type, description: m.description })));
        
        moments.forEach((moment, index) => {
            console.log(`[Timeline] 创建描述项 ${index + 1}: time=${moment.time}s, type=${moment.type}, description=${moment.description}`);
            try {
                const descriptionItem = this.createDescriptionItem(moment, index);
                descriptionsList.appendChild(descriptionItem);
                console.log(`[Timeline] 描述项 ${index + 1} 创建成功`);
            } catch (error) {
                console.error(`[Timeline] 创建描述项 ${index + 1} 失败:`, error, moment);
            }
        });
        
        descriptionsContainer.appendChild(descriptionsList);
        console.log('[Timeline] 描述列表已添加到容器');
        
        // 确保容器可见
        descriptionsContainer.style.display = 'block';
        descriptionsContainer.style.visibility = 'visible';
        descriptionsContainer.style.opacity = '1';
        
        // 数据一致性验证：检查渲染后的内容
        const renderedItems = descriptionsContainer.querySelectorAll('.timeline-description-item');
        console.log(`[Timeline] 已渲染${moments.length}个时间点描述，实际DOM元素数: ${renderedItems.length}`);
        
        // 验证每个渲染项的时间值
        renderedItems.forEach((item, index) => {
            const itemTime = parseInt(item.dataset.time);
            const expectedTime = moments[index]?.time;
            if (itemTime !== expectedTime) {
                console.error(`[Timeline] 数据不一致！描述项 ${index + 1}: DOM显示时间=${itemTime}s, 期望时间=${expectedTime}s`);
            } else {
                console.log(`[Timeline] 数据一致 ✓ 描述项 ${index + 1}: time=${itemTime}s`);
            }
        });
        
        console.log('[Timeline] 描述容器位置:', descriptionsContainer.parentNode ? descriptionsContainer.parentNode.className : '无父节点');
        console.log('[Timeline] 描述容器样式:', window.getComputedStyle(descriptionsContainer).display);
        console.log('[Timeline] 描述容器内容长度:', descriptionsContainer.innerHTML.length);
    }

    createDescriptionItem(moment, index) {
        // 详细日志：记录输入数据
        const formattedTime = this.formatTime(moment.time);
        console.log(`[Timeline Description] 创建描述项 ${index + 1} - 输入数据:`, {
            momentTime: moment.time,
            momentType: moment.type,
            momentDescription: moment.description,
            formattedTime: formattedTime,
            timeType: typeof moment.time,
            hasKnowledge: !!moment.knowledge
        });
        
        const item = document.createElement('div');
        item.className = 'timeline-description-item';
        item.dataset.type = moment.type;
        item.dataset.time = moment.time;
        
        // 类型颜色映射
        const typeColors = {
            '开始': '#28a745',
            '阶段': '#ffc107',
            '关键': '#dc3545'
        };
        const typeIcons = {
            '开始': '🟢',
            '阶段': '🟡',
            '关键': '🔴'
        };
        const color = typeColors[moment.type] || '#667eea';
        const icon = typeIcons[moment.type] || '⚪';
        
        // 获取相关知识
        const knowledge = moment.knowledge || {};
        const tips = knowledge.tips || [];
        
        // 构建HTML
        item.innerHTML = `
            <div class="description-item-header">
                <span class="description-type-badge" style="background-color: ${color}20; color: ${color}; border-color: ${color};">
                    ${icon} ${moment.type}
                </span>
                <span class="description-time">${formattedTime}</span>
            </div>
            <div class="description-item-content">
                <h5 class="description-title">${moment.description}</h5>
                ${knowledge.content ? `<p class="description-text">${knowledge.content}</p>` : ''}
                ${tips.length > 0 ? `
                    <div class="description-tips">
                        <strong>${window.i18n ? window.i18n.t('action_analysis.tips', '技术要点：') : '要点提示：'}</strong>
                        <ul>
                            ${tips.map(tip => `<li>${tip}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
            <button class="description-seek-btn" data-time="${moment.time}">
                <i class="fas fa-play"></i> ${window.i18n ? window.i18n.t('timeline.seek_to_time', '跳转到此时间点') : '跳转到此时间点'}
            </button>
        `;
        
        // 添加点击跳转功能
        const seekBtn = item.querySelector('.description-seek-btn');
        seekBtn.addEventListener('click', () => {
            this.seekToTime(moment.time);
            // 高亮当前项
            document.querySelectorAll('.timeline-description-item').forEach(el => {
                el.classList.remove('active');
            });
            item.classList.add('active');
        });
        
        // 添加点击整个项也可以跳转
        item.addEventListener('click', (e) => {
            if (e.target !== seekBtn && !seekBtn.contains(e.target)) {
                this.seekToTime(moment.time);
                document.querySelectorAll('.timeline-description-item').forEach(el => {
                    el.classList.remove('active');
                });
                item.classList.add('active');
            }
        });
        
        // 详细日志：记录创建完成后的数据
        const actualTime = parseInt(item.dataset.time);
        const actualType = item.dataset.type;
        const displayedTime = item.querySelector('.description-time')?.textContent;
        console.log(`[Timeline Description] 描述项 ${index + 1} 创建完成:`, {
            actualTime: actualTime,
            expectedTime: moment.time,
            timeMatch: actualTime === moment.time,
            actualType: actualType,
            expectedType: moment.type,
            typeMatch: actualType === moment.type,
            displayedTime: displayedTime,
            formattedTime: formattedTime,
            displayMatch: displayedTime === formattedTime
        });
        
        return item;
    }

    createMarker(moment, videoDuration) {
        const marker = document.createElement('div');
        // 使用data属性来标识类型，避免中文类名问题
        marker.className = 'timeline-marker';
        marker.dataset.time = moment.time;
        marker.dataset.type = moment.type;
        marker.title = `${moment.description} - ${this.formatTime(moment.time)}`;

        // 详细日志：记录输入数据
        console.log(`[Timeline Marker] 创建标记 - 输入数据:`, {
            momentTime: moment.time,
            momentType: moment.type,
            momentDescription: moment.description,
            videoDuration: videoDuration,
            timeType: typeof moment.time,
            durationType: typeof videoDuration
        });

        // 根据时间计算位置百分比
        if (videoDuration > 0) {
            const positionPercent = Math.min(100, Math.max(0, (moment.time / videoDuration) * 100));
            const calculatedLeft = `${positionPercent}%`;
            marker.style.left = calculatedLeft;
            marker.style.transform = 'translateX(-50%) translateY(-50%)'; // 居中显示
            marker.style.position = 'absolute'; // 确保绝对定位
            marker.style.top = '50%';
            
            // 详细日志：记录计算结果和实际设置的值
            console.log(`[Timeline Marker] 标记创建完成:`, {
                type: moment.type,
                time: moment.time,
                videoDuration: videoDuration,
                positionPercent: positionPercent.toFixed(2),
                calculatedLeft: calculatedLeft,
                actualLeft: marker.style.left,
                formattedTime: this.formatTime(moment.time)
            });
        } else {
            // 如果没有视频时长，使用默认位置
            marker.style.left = '0%';
            marker.style.transform = 'translateY(-50%)';
            marker.style.position = 'absolute';
            marker.style.top = '50%';
            console.warn(`[Timeline Marker] 视频时长为0，时间点${moment.type}使用默认位置`, {
                momentTime: moment.time,
                videoDuration: videoDuration
            });
        }

        const dot = document.createElement('div');
        dot.className = 'marker-dot';
        // 根据类型直接设置颜色（优先使用内联样式，确保颜色正确显示）
        this.setMarkerColor(dot, moment.type);
        marker.appendChild(dot);

        const label = document.createElement('div');
        label.className = 'marker-label';
        label.textContent = this.formatTime(moment.time);
        marker.appendChild(label);

        // 点击跳转
        marker.addEventListener('click', () => {
            this.seekToTime(moment.time);
            this.showKnowledgeCard(moment);
        });

        // 添加鼠标悬停效果
        marker.addEventListener('mouseenter', () => {
            dot.style.transform = 'scale(1.5)';
        });
        marker.addEventListener('mouseleave', () => {
            dot.style.transform = 'scale(1)';
        });

        return marker;
    }

    setMarkerColor(dotElement, type) {
        // 直接设置颜色，避免CSS选择器问题
        const colors = {
            '开始': '#28a745',  // 绿色
            '阶段': '#ffc107',  // 黄色
            '关键': '#dc3545'   // 红色
        };
        const color = colors[type] || '#667eea'; // 默认蓝色
        // 使用!important确保样式生效
        dotElement.setAttribute('style', `
            background: ${color} !important;
            border: 2px solid ${color} !important;
            box-shadow: 0 0 6px ${color}80 !important;
            width: 14px !important;
            height: 14px !important;
            border-radius: 50% !important;
            margin: 0 auto !important;
            transition: all 0.2s !important;
        `);
        console.log(`[Timeline] 设置时间点颜色: type=${type}, color=${color}`);
    }

    seekToTime(time) {
        if (window.youtubeSystem && window.youtubeSystem.player) {
            // 如果使用YouTube Player API
            if (window.youtubeSystem.player.seekTo) {
                window.youtubeSystem.player.seekTo(time, true);
            } else {
                // 使用URL参数跳转
                const iframe = window.youtubeSystem.player;
                if (iframe && iframe.src) {
                    const newUrl = iframe.src.split('&start=')[0] + `&start=${time}`;
                    iframe.src = newUrl;
                }
            }
        }
    }

    showKnowledgeCard(moment) {
        if (moment.knowledge && window.knowledgeCardSystem) {
            window.knowledgeCardSystem.showCardAtTime(moment.time, {
                type: moment.type,
                title: moment.knowledge.title,
                content: moment.knowledge.content,
                tips: moment.knowledge.tips || []
            });
        }
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    getVideoDuration() {
        // 详细日志：记录所有可能的时长来源
        console.log('[Timeline Duration] 开始获取视频时长...');
        console.log('[Timeline Duration] 当前状态:', {
            savedDuration: this.videoDuration,
            hasYoutubeSystem: !!window.youtubeSystem,
            hasCurrentVideo: !!(window.youtubeSystem && window.youtubeSystem.currentVideo),
            momentsCount: this.moments.length
        });
        
        // 优先使用保存的视频时长
        if (this.videoDuration > 0) {
            console.log(`[Timeline Duration] ✅ 使用保存的视频时长: ${this.videoDuration}秒`);
            return this.videoDuration;
        }
        
        // 从youtubeSystem获取
        if (window.youtubeSystem && window.youtubeSystem.currentVideo) {
            const currentVideo = window.youtubeSystem.currentVideo;
            let duration = 0;
            
            // 尝试多种方式获取时长
            if (typeof currentVideo.duration === 'number') {
                duration = currentVideo.duration;
            } else if (typeof currentVideo.duration === 'string') {
                // 如果是字符串格式（如"5:30"），尝试解析
                const parts = currentVideo.duration.split(':').map(Number);
                if (parts.length === 2) {
                    duration = parts[0] * 60 + parts[1];
                } else if (parts.length === 3) {
                    duration = parts[0] * 3600 + parts[1] * 60 + parts[2];
                }
            }
            
            if (duration > 0) {
                console.log(`[Timeline Duration] ✅ 从youtubeSystem获取时长: ${duration}秒`, {
                    rawDuration: currentVideo.duration,
                    parsedDuration: duration
                });
                // 保存获取到的时长
                this.videoDuration = duration;
                return duration;
            } else {
                console.warn('[Timeline Duration] ⚠️ youtubeSystem中的时长无效:', currentVideo.duration);
            }
        } else {
            console.warn('[Timeline Duration] ⚠️ 无法从youtubeSystem获取时长:', {
                hasYoutubeSystem: !!window.youtubeSystem,
                hasCurrentVideo: !!(window.youtubeSystem && window.youtubeSystem.currentVideo)
            });
        }
        
        // 从moments中推断最大时长
        if (this.moments.length > 0) {
            const maxTime = Math.max(...this.moments.map(m => m.time));
            const estimatedDuration = maxTime * 1.5; // 估算总时长（最大时间点的1.5倍）
            console.log(`[Timeline Duration] ⚠️ 从moments推断时长: ${estimatedDuration}秒 (最大时间点: ${maxTime}秒)`);
            return estimatedDuration;
        }
        
        console.warn('[Timeline Duration] ⚠️ 无法获取视频时长，使用默认值300秒');
        return 300; // 默认5分钟
    }

    addMoment(moment) {
        this.moments.push(moment);
        this.moments.sort((a, b) => a.time - b.time);
        this.renderTimeline();
    }

    /**
     * 验证时间点数据的完整性
     * @param {Array} moments - 要验证的时间点数组
     * @returns {Object} 验证结果 {valid: boolean, errors: Array}
     */
    validateMomentsData(moments) {
        const errors = [];
        
        if (!Array.isArray(moments)) {
            errors.push('moments 不是数组');
            return { valid: false, errors };
        }
        
        if (moments.length === 0) {
            return { valid: true, errors: [], message: '空数组（这是有效的）' };
        }
        
        moments.forEach((moment, index) => {
            if (!moment) {
                errors.push(`索引 ${index}: moment 为 null 或 undefined`);
                return;
            }
            
            if (typeof moment.time !== 'number' || isNaN(moment.time)) {
                errors.push(`索引 ${index}: time 不是有效数字 (${moment.time})`);
            }
            
            if (moment.time < 0) {
                errors.push(`索引 ${index}: time 为负数 (${moment.time})`);
            }
            
            if (!moment.type || typeof moment.type !== 'string') {
                errors.push(`索引 ${index}: type 无效 (${moment.type})`);
            }
            
            if (!moment.description || typeof moment.description !== 'string') {
                errors.push(`索引 ${index}: description 无效 (${moment.description})`);
            }
        });
        
        // 检查时间值是否重复
        const times = moments.map(m => m.time);
        const uniqueTimes = new Set(times);
        if (times.length !== uniqueTimes.size) {
            errors.push('存在重复的时间值');
        }
        
        // 检查是否按时间排序
        for (let i = 1; i < moments.length; i++) {
            if (moments[i].time < moments[i - 1].time) {
                errors.push('时间点未按时间顺序排列');
                break;
            }
        }
        
        const valid = errors.length === 0;
        if (valid) {
            console.log(`[Timeline] 数据验证通过: ${moments.length}个时间点，时间范围: ${moments[0].time}s - ${moments[moments.length - 1].time}s`);
        } else {
            console.error(`[Timeline] 数据验证失败，发现 ${errors.length} 个错误:`, errors);
        }
        
        return { valid, errors, momentsCount: moments.length };
    }

    /**
     * 验证时间轴标记和描述项的一致性
     * @param {Array} expectedMoments - 期望的时间点数据
     * @param {number} videoDuration - 视频时长
     */
    validateTimelineConsistency(expectedMoments, videoDuration) {
        console.log('[Timeline Validation] 开始验证时间轴一致性...');
        
        // 获取所有时间轴标记
        const markers = this.timelineContainer.querySelectorAll('.timeline-marker');
        // 获取所有描述项
        const descriptions = document.querySelectorAll('.timeline-description-item');
        
        console.log('[Timeline Validation] 数据统计:', {
            expectedMomentsCount: expectedMoments.length,
            actualMarkersCount: markers.length,
            actualDescriptionsCount: descriptions.length,
            videoDuration: videoDuration
        });
        
        // 验证数量一致性
        if (markers.length !== expectedMoments.length) {
            console.error(`[Timeline Validation] ❌ 标记数量不一致: 期望${expectedMoments.length}个，实际${markers.length}个`);
        }
        if (descriptions.length !== expectedMoments.length) {
            console.error(`[Timeline Validation] ❌ 描述项数量不一致: 期望${expectedMoments.length}个，实际${descriptions.length}个`);
        }
        
        // 验证每个时间点的数据一致性
        const inconsistencies = [];
        expectedMoments.forEach((expectedMoment, index) => {
            const marker = markers[index];
            const description = descriptions[index];
            
            const markerTime = marker ? parseInt(marker.dataset.time) : null;
            const markerType = marker ? marker.dataset.type : null;
            const markerPosition = marker ? marker.style.left : null;
            
            const descTime = description ? parseInt(description.dataset.time) : null;
            const descType = description ? description.dataset.type : null;
            const descDisplayTime = description ? description.querySelector('.description-time')?.textContent : null;
            
            // 计算期望的位置
            const expectedPosition = videoDuration > 0 
                ? `${(expectedMoment.time / videoDuration * 100).toFixed(2)}%` 
                : '0%';
            
            // 验证时间值
            if (markerTime !== expectedMoment.time) {
                inconsistencies.push({
                    index: index + 1,
                    type: 'marker_time_mismatch',
                    expected: expectedMoment.time,
                    actual: markerTime,
                    location: '时间轴标记'
                });
            }
            
            if (descTime !== expectedMoment.time) {
                inconsistencies.push({
                    index: index + 1,
                    type: 'description_time_mismatch',
                    expected: expectedMoment.time,
                    actual: descTime,
                    location: '描述项'
                });
            }
            
            // 验证类型
            if (markerType !== expectedMoment.type) {
                inconsistencies.push({
                    index: index + 1,
                    type: 'marker_type_mismatch',
                    expected: expectedMoment.type,
                    actual: markerType,
                    location: '时间轴标记'
                });
            }
            
            if (descType !== expectedMoment.type) {
                inconsistencies.push({
                    index: index + 1,
                    type: 'description_type_mismatch',
                    expected: expectedMoment.type,
                    actual: descType,
                    location: '描述项'
                });
            }
            
            // 验证位置
            if (marker && Math.abs(parseFloat(markerPosition) - parseFloat(expectedPosition)) > 0.1) {
                inconsistencies.push({
                    index: index + 1,
                    type: 'marker_position_mismatch',
                    expected: expectedPosition,
                    actual: markerPosition,
                    location: '时间轴标记位置'
                });
            }
            
            // 验证显示时间
            const expectedFormattedTime = this.formatTime(expectedMoment.time);
            if (descDisplayTime !== expectedFormattedTime) {
                inconsistencies.push({
                    index: index + 1,
                    type: 'description_display_time_mismatch',
                    expected: expectedFormattedTime,
                    actual: descDisplayTime,
                    location: '描述项显示时间'
                });
            }
            
            // 输出每个时间点的详细信息
            console.log(`[Timeline Validation] 时间点 ${index + 1}:`, {
                expected: {
                    time: expectedMoment.time,
                    type: expectedMoment.type,
                    formattedTime: expectedFormattedTime,
                    position: expectedPosition
                },
                marker: {
                    time: markerTime,
                    type: markerType,
                    position: markerPosition,
                    match: markerTime === expectedMoment.time && markerType === expectedMoment.type
                },
                description: {
                    time: descTime,
                    type: descType,
                    displayTime: descDisplayTime,
                    match: descTime === expectedMoment.time && descType === expectedMoment.type && descDisplayTime === expectedFormattedTime
                }
            });
        });
        
        // 输出验证结果
        if (inconsistencies.length === 0) {
            console.log('[Timeline Validation] ✅ 所有数据一致性验证通过！');
        } else {
            console.error(`[Timeline Validation] ❌ 发现 ${inconsistencies.length} 个不一致项:`, inconsistencies);
            inconsistencies.forEach(inc => {
                console.error(`  - ${inc.location} (索引${inc.index}): 期望 ${inc.expected}, 实际 ${inc.actual}`);
            });
        }
        
        return {
            valid: inconsistencies.length === 0,
            inconsistencies: inconsistencies,
            markersCount: markers.length,
            descriptionsCount: descriptions.length,
            expectedCount: expectedMoments.length
        };
    }
}

// 初始化
window.timelineAnnotator = new TimelineAnnotator();

