 document.querySelector(".download-btn").addEventListener("click", function() {
      this.innerText = "Downloading...";
      setTimeout(() => {
          this.innerHTML = '<i class="fa-solid fa-download"></i> Download CV';
      }, 2000); // Reset text after 2 seconds
    });
