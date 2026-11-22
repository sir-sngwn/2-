//
//  popup.mm
//  방중 프로젝트 - Native Floating Warning Popup
//
#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>

int main(int argc, char* argv[]) {
    @autoreleasepool {
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];

        NSRect frame = NSMakeRect(0, 0, 300, 300);
        NSWindow* window = [[NSWindow alloc] initWithContentRect:frame
                                                       styleMask:(NSWindowStyleMaskTitled | NSWindowStyleMaskClosable)
                                                         backing:NSBackingStoreBuffered
                                                           defer:NO];
        [window center];
        [window setLevel:NSFloatingWindowLevel];
        [window setTitle:@"⚠️ Focus Alert"];
        [window setBackgroundColor:[NSColor blackColor]];

        WKWebViewConfiguration* config = [[WKWebViewConfiguration alloc] init];
        WKWebView* webView = [[WKWebView alloc] initWithFrame:[[window contentView] bounds] configuration:config];
        [webView setAutoresizingMask:(NSViewWidthSizable | NSViewHeightSizable)];
        [[window contentView] addSubview:webView];

        if (argc > 1) {
            NSString* path = [NSString stringWithUTF8String:argv[1]];
            NSURL* url = [NSURL fileURLWithPath:path];
            [webView loadFileURL:url allowingReadAccessToURL:[url URLByDeletingLastPathComponent]];
        }

        [window makeKeyAndOrderFront:nil];
        [NSApp activateIgnoringOtherApps:YES];
        [NSApp run];
    }
    return 0;
}
