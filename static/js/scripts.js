// Initialize carousel
$(document).ready(function(){
    // Auto-advance carousel every 5 seconds
    $('.carousel').carousel({
        interval: 5000
    });
    
    // Add floating hearts dynamically
    for (let i = 0; i < 10; i++) {
        $('.hearts-background').append('<div>❤</div>');
    }
    
    // Add animation to welcome message
    setTimeout(function() {
        $('.welcome-message').addClass('animate__heartBeat');
    }, 1500);
});