// Example event listener.
// Event argument will always be {eventType, args} dict

EventHandler.registerCallback(IBOM_EVENT_TYPES.ALL, (e) => console.log(e));

// Example custom metadata (use with userheader.html)
window.addEventListener("load", function () {
  var meta = {};
  try {
    console.log(typeof config.custom_metadata_field);
    console.log(JSON.stringify(config.custom_metadata_field));
    meta = JSON.parse(config.custom_metadata_field || "{}");
  } catch (e) {
    console.error("custom_metadata is no valid JSON string:", e);
  }

  var element = document.getElementById("custom-metadata");
  if (!element) return;

  var text = "Drawing: " + (meta.drawing || "-") +
             " | Customer: " + (meta.customer || "-");

  element.textContent = text;
});
