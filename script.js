const menuButton = document.getElementById("menuButton");
const closeButton = document.getElementById("closeButton");
const menu = document.getElementById("menu");

menuButton.addEventListener("click", function () {

    menu.classList.add("open");

});

closeButton.addEventListener("click", function () {

    menu.classList.remove("open");

});

const menuLinks = document.querySelectorAll(".menu a");

menuLinks.forEach(function (link) {

    link.addEventListener("click", function () {

        menu.classList.remove("open");

    });

});