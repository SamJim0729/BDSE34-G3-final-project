document.addEventListener("DOMContentLoaded", function() {
    const members = [
        {
            name: "組員1",
            role: "負責工作1",
            img: "static/assets/img/members/member1.png"
        },
        {
            name: "組員2",
            role: "負責工作2",
            img: "static/assets/img/members/member2.png"
        },
        // 其他組員資料
        {
            name: "組員3",
            role: "負責工作3",
            img: "static/assets/img/members/member3.png"
        },
        {
            name: "組員4",
            role: "負責工作4",
            img: "static/assets/img/members/member4.png"
        },
        {
            name: "組員5",
            role: "負責工作5",
            img: "static/assets/img/members/member5.png"
        },
        {
            name: "組員6",
            role: "負責工作6",
            img: "static/assets/img/members/member6.png"
        },
        {
            name: "組員7",
            role: "負責工作7",
            img: "static/assets/img/members/member7.png"
        }
    ];

    let currentIndex = 0;

    function displayMember(index) {
        const memberInfo = document.getElementById("member-info");
        memberInfo.innerHTML = `
            <img src="${members[index].img}" alt="${members[index].name}" class="member-img">
            <h3>${members[index].name}</h3>
            <p>${members[index].role}</p>
        `;
        updateDots(index);
    }

    function updateDots(index) {
        const dots = document.querySelectorAll(".carousel-dots .dot");
        dots.forEach((dot, i) => {
            dot.classList.toggle("active", i === index);
        });
    }

    document.querySelectorAll(".carousel-dots .dot").forEach(dot => {
        dot.addEventListener("click", function() {
            const index = parseInt(this.getAttribute("data-index"));
            currentIndex = index;
            displayMember(currentIndex);
        });
    });
    
    // 新增滑動事件監聽
    let touchStartX = 0;
    let touchEndX = 0;

    function handleGesture() {
        if (touchEndX < touchStartX) {
            currentIndex = (currentIndex + 1) % members.length;
        }
        if (touchEndX > touchStartX) {
            currentIndex = (currentIndex - 1 + members.length) % members.length;
        }
        displayMember(currentIndex);
    }

    const memberInfo = document.getElementById("member-info");

    // 手機觸摸事件
    memberInfo.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    });

    memberInfo.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleGesture();
    });

    // 桌面版滑鼠拖拉事件
    memberInfo.addEventListener('mousedown', e => {
        touchStartX = e.screenX;
    });

    memberInfo.addEventListener('mouseup', e => {
        touchEndX = e.screenX;
        handleGesture();
    });

    // 初始顯示第一個組員
    displayMember(currentIndex);
});